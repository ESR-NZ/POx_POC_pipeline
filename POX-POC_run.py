#!/usr/bin/env python

from pathlib import Path
from subprocess import Popen, PIPE, run
import argparse
import os
import shutil
from pox_poc import plotting, qc, klassifier


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


# path constants
minKnow_run_path = Path(args.minKnow_run_path) 


# Will put results in the minKnow dir for now
RESULTS_PATH = minKnow_run_path/"POx_POC_Results"
# Make the results directory. Overwrite if exists.
if RESULTS_PATH.is_dir():
    shutil.rmtree(RESULTS_PATH)
RESULTS_PATH.mkdir()


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
    # filter some unwanted dirs
    filtered_fastq_dirs = [p for p in all_fastq_dirs if "fastq_fail" not in p.parts and p.name != "unclassified"]
    
    return filtered_fastq_dirs 


def is_gz_file(file_path: Path) -> bool:
    '''
    dirty trick to check for gzipped files based on magic number first 2 bites
    '''
    with open(file_path, 'rb') as f:
        is_gzip = f.read(2) == b'\x1f\x8b'

        return is_gzip


# concat reads for each "barcode" to single file for analysis
def concat_read_files(fq_dir: Path) -> Path:
    '''
    Takes in a Path object of a directory of fastq files and combines them
    into a singe file within that same directory. The function then returns
    the path to this new file. This uses the unix cat command.
    Could probably make this more parallel...   
    '''
    all_reads = Path(f"{fq_dir / fq_dir.name}_all_reads") 
    
    # remove any tmp files from previous crashed runs
    # this works but is ugly, needs attention
    if all_reads.with_suffix('.fastq').is_file():
        os.remove(all_reads.with_suffix('.fastq'))
    if all_reads.with_suffix('.fastq.gz').is_file():
        os.remove(all_reads.with_suffix('.fastq.gz'))
    

    print(f'Concatenating all fastq read files to {all_reads.name}') # print for debug
    cat_cmd = f"cat {fq_dir}/*.fastq* > {all_reads}"
    
    # run the command with supprocess.run 
    run(cat_cmd, shell=True, check=True)
    
    # add the correct suffix to the file based on gzip'd or not
    # this works but is ugly, needs attention
    if is_gz_file(all_reads):
        all_reads.replace(all_reads.with_suffix('.fastq.gz'))
        all_reads_suffix = all_reads.parent / (all_reads.name + '.fastq.gz')
    else:
        all_reads.replace(all_reads.with_suffix('.fastq')) 
        all_reads_suffix = all_reads.parent / (all_reads.name + '.fastq')
    
    print(bcolors.HEADER + f"{all_reads_suffix}" + bcolors.ENDC)
    
    return all_reads_suffix



####################### main func to run the script ################
def main():
    print("\nRunning POX-POC pipeline")
    print("\nLooking for all your samples in run: " + bcolors.HEADER + f"{minKnow_run_path}\n" + bcolors.ENDC)
    fastq_dirs = get_fastq_dirs(minKnow_run_path)

    for fq_dir in sorted(fastq_dirs):
        
        # Get barcode for this sample
        BARCODE=fq_dir.name.split('_')[0]

        print("\nNow working on: " + bcolors.RED + f"{BARCODE}\n" + bcolors.ENDC)
        print("Checking read numbers for: " + bcolors.RED + f"{BARCODE}\n" + bcolors.ENDC)
        
        # Gather the reads and assign Path of reads to 'fastq_file'
        # This asignment is a dumb way to do this
        fastq_file = concat_read_files(fq_dir)
        
        # Filter the reads and assign the Path of the filtered reads to 'len_filtered_fastq'
        len_filtered_fastq = qc.run_seqkit_lenght_filter(fastq_file)
        
        print("Filtered reads live at: " + bcolors.HEADER + f"{len_filtered_fastq}\n" + bcolors.ENDC)
        
        print(f'Calc length array for ' + bcolors.RED + f"{BARCODE}\n" + bcolors.ENDC)
        lens_array = qc.get_lens_array(len_filtered_fastq)
        num_reads = len(lens_array)

        if num_reads < 1000:
            print(f'Skiping sample {BARCODE}, not enough reads\n')
            continue

        print(f'Passed reads: ' + bcolors.RED + f"{num_reads}\n" + bcolors.ENDC)
        
        # Do some plotting of the passed reads
        if not plotting.plot_length_dis_graph(fq_dir, BARCODE, lens_array, RESULTS_PATH):
            # need to clean up the temp files here
            os.remove(fastq_file)
            os.remove(len_filtered_fastq)
            continue

        # Run the classifer and unpack the tuple of Paths of the output files to vars
        KREPORT_PATH = klassifier.kraken2_run(len_filtered_fastq, BARCODE, RESULTS_PATH)[1]
        
        # parsing the k2 report to get top hits
        species_dict = klassifier.parse_kraken(BARCODE, KREPORT_PATH)
        
        # writing the tophits to a file, probalby crash if there are no hits
        # needs attention
        top_species = klassifier.write_classify_to_file(species_dict, RESULTS_PATH)

        print(bcolors.YELLOW + "\nTop classifiction hit: " + bcolors.BLUE + f"{top_species}\n" + bcolors.ENDC)

        # need to clean up the temp files here
        os.remove(fastq_file)
        os.remove(len_filtered_fastq)

    print(bcolors.YELLOW + "\nPOx_POC finished! Results are in: " + bcolors.HEADER + f"{RESULTS_PATH}" + bcolors.ENDC)
    print(bcolors.YELLOW + "\nThanks!" + bcolors.ENDC)

if __name__ == '__main__':
    main()
