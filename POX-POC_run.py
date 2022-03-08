#!/usr/bin/env python

from pathlib import Path
import argparse
import os
import shutil
from pox_poc import plotting, qc, klassifier
from datetime import date

# terminal text color
class bcolors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'

# eg print(bcolors.GREEN + "This text is green" + bcolors.RED + " and this is RED...?" + bcolors.ENDC)
# print(bcolors.GREEN + "" + bcolors.ENDC)

# Pipe line needs a single positional arg that points to a run directory
arg_parser = argparse.ArgumentParser(prog='POx-POC analysis pipeline',
                                description="Run the POx-POC analysis pipeline for all sub-directories with sequencing reads inside")

arg_parser.add_argument("minKnow_run_path",
                        metavar='path',
                        type=str,
                        help='Path to the MinKnow output directory of the sequencing run you wish to analyse')

args = arg_parser.parse_args()

# Path constants
minKnow_run_path = Path(args.minKnow_run_path) 

# check if the supplied run_path is a valid directory, if not exit gracefully
if not minKnow_run_path.is_dir():
    print(bcolors.RED + "Supplied path is not a directory. Check the spelling of your path. Exiting..." + bcolors.ENDC)
    exit()

# Put results in a dated sub-directory of the supplied minKnow directory
date_today = date.today()
RESULTS_PATH = minKnow_run_path/f"POx_POC_Results_{date_today}"

# Make the results directory. Overwrite if exists.
if RESULTS_PATH.is_dir():
    shutil.rmtree(RESULTS_PATH)
RESULTS_PATH.mkdir()

# Set up more sub-directories for each result type
# make a dir for the combinred fastq files
COMBINED_FASTQ_DIR = RESULTS_PATH/"Combined_fastqs"
COMBINED_FASTQ_DIR.mkdir()

# make a dir for the kreport files
KREPORT_DIR = RESULTS_PATH/"Classification_report_files"
KREPORT_DIR.mkdir()

# make a dir for the plots
PLOT_DIR = RESULTS_PATH/"Plots"
PLOT_DIR.mkdir()


# Get a list of directories with fastqs in them, this works if multiplexed or not
def get_fastq_dirs(minKnow_run_path):
    '''
    Takes the top level run directory spawned by the sequencer run 
    as a Path object and returns an list of Path objects for the sub directories 
    that have fastqs in them. Any dir with a .fastq(.gz) in it will be treated as a "sample".
    The directory name will become the samples barcode name. 
    Finally, filter out fastq_fail and unclassified dirs. 
    If two samples have the same name the second to be processed will overwrite the first.   
    '''
    # get path to every fastq file under the supplied run_path
    fq_glob_paths = [fq_dir for fq_dir in minKnow_run_path.rglob('*.fastq*')] 
    # get the set of all dirs with fastq files 
    all_fastq_dirs = {fq_path.parent for fq_path in fq_glob_paths}
    # filter some unwanted dirs ie unclassified and fastq_fail
    filtered_fastq_dirs = [p for p in all_fastq_dirs if "fastq_fail" not in p.parts and p.name != "unclassified"]
    # and filter out any Combined_fastqs dirs
    filtered_fastq_dirs = [p for p in filtered_fastq_dirs if "Combined_fastqs" not in p.parts]

    return filtered_fastq_dirs 

####################### main func to run the script ################
def main():
    print("\nRunning POX-POC pipeline")
    print("\nLooking for all your samples in run: " + bcolors.HEADER + f"{minKnow_run_path}\n" + bcolors.ENDC)
    
    # all fastq dirs (barcodes) in the run dir
    fastq_dirs = get_fastq_dirs(minKnow_run_path)

    # loop through all fastq dirs (barcodes)
    for fq_dir in sorted(fastq_dirs):
        
        # Get barcode for this sample by parsing the dir name
        BARCODE=fq_dir.name.split('_')[0]

        print("\nNow working on: " + bcolors.RED + f"{BARCODE}\n" + bcolors.ENDC)
        print("Checking read numbers for: " + bcolors.RED + f"{BARCODE}\n" + bcolors.ENDC)
        
        # Gather the reads and assign Path of reads to 'fastq_files'
        # resulting file needs to be cleaned up later
        fastq_file = qc.concat_read_files(fq_dir, COMBINED_FASTQ_DIR)
        
        # Filter the reads and assign the Path of the filtered reads to 'len_filtered_fastq'
        # resulting file needs to be cleaned up later
        filter_length=1000
        len_filtered_fastq = qc.run_seqkit_lenght_filter(fastq_file, BARCODE, COMBINED_FASTQ_DIR, filter_length)

        print("Filtered reads live at: " + bcolors.HEADER + f"{len_filtered_fastq}\n" + bcolors.ENDC)
        
        print(f'Calc length array for ' + bcolors.RED + f"{BARCODE}\n" + bcolors.ENDC)
        lens_array = qc.get_lens_array(len_filtered_fastq)
        
        # get the number of reads in the length filtered fastq file
        num_reads = len(lens_array)
        
        # skip barcodes with less than 1000 reads
        if num_reads < 1000:
            print(f'Skiping sample {BARCODE}, not enough reads\n')
            # remove the fastq file and the filtered reads
            os.remove(fastq_file)
            os.remove(len_filtered_fastq)
            continue

        print(f'Passed reads: ' + bcolors.RED + f"{num_reads}\n" + bcolors.ENDC)

        # Get the QC data for the filtered data and write to a dict
        # get N50
        N50 = qc.func_N50(lens_array)
        
        # total bases in the length filtered fastq file
        total_base_count = qc.count_fastq_bases(len_filtered_fastq)

        qc_dict = {"N50": N50, 
            "total_bases_count": total_base_count, 
            "number_of_reads": num_reads, 
            "BARCODE": BARCODE,
            "filter_length": filter_length,
            "lens_array": lens_array}

        # Do some plotting of the length filtered fastq file
        plotting.plot_length_dis_graph(qc_dict, PLOT_DIR)

        # Run the classifer and unpack the tuple of Paths of the output files to vars
        K_PATHS = klassifier.kraken2_run(len_filtered_fastq, BARCODE, KREPORT_DIR)
        kreport=K_PATHS[0]

        # parsing the k2 report to get top hits
        species_dict = klassifier.parse_kraken(BARCODE, kreport)
        

        # add the qc data to the species dict
        species_dict.update(qc_dict)

        # writing the top-hits to a file, this is a csv file
        # writes to a file called "classification_results.csv"
        top_species = klassifier.write_classify_to_file(species_dict, RESULTS_PATH)
        

        print(bcolors.YELLOW + "\nTop classifiction hit: " + bcolors.BLUE + f"{top_species}\n" + bcolors.ENDC)

        # cleanup combined fastq_file, keep length filtered file for downstream analysis
        os.remove(fastq_file)
        

    print(bcolors.YELLOW + "\nPOx_POC finished! Results are in: " + bcolors.HEADER + f"{RESULTS_PATH}" + bcolors.ENDC)
    print(bcolors.YELLOW + "\nThanks!" + bcolors.ENDC)

if __name__ == '__main__':
    main()
