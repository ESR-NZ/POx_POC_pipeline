#!/usr/bin/env python

from pathlib import Path
from Bio import SeqIO
from subprocess import Popen, PIPE, run
import numpy as np
import seaborn as sns
from matplotlib import pyplot as plt
import re
import gzip
import argparse
import csv
import os
import shutil


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

KRAKEN2_DB_PATH=os.environ.get('KRAKEN2_DB_PATH')

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


# Function for data QC
def get_lens_array(fastq_file):
    '''
    Takes in a single fastq file and returns and list of the legths of each read
    in the file. Used to calc the N50 and histogram.
    Have identified that this can be done much faster with unix or Rust. 
    This will surfice for the draft script for now.
    '''
    ## this needs to handle gzipped files
    if is_gz_file(fastq_file):
        with gzip.open(fastq_file, "rt") as gz_file:
            lens_array = [len(rec) for rec in SeqIO.parse(gz_file, "fastq")]
               
    else:
        lens_array = [len(rec) for rec in SeqIO.parse(fastq_file, "fastq")]
    
    return lens_array


def func_N50(lens_array):
    '''
    Does what it says on the tin. Takes in the read lenths array and spits out the N50 stat
    Fast approximation calc. 
    '''
    lens_array.sort()
    
    #half of the total data
    half_sum = sum(lens_array)/2
    cum_sum = 0
    # find the lenght of the read that is at least half the total data length 
    for v in lens_array:
        cum_sum += v
        if cum_sum >= half_sum:
            return int(v)


def count_fastq_bases(fastq_file):
    '''
    counts the number of bases sequenced in a fastq file
    '''
    # the command, as a string, that will be used in a bash subprocess to do the calculation
    cat_cmd = f"cat {fastq_file} | paste - - - - | cut -f 2 | tr -d '\n' | wc -c"
    # span a subprocess and run the command
    sp = Popen(cat_cmd, shell=True, stdout=PIPE) # people dont like 'shell = true'
    # get the results back from the sp
    bases = sp.communicate()[0]
    
    return int(bases.decode('ascii').rstrip())


def plot_length_dis_graph(fq_dir, BARCODE, lens_array, results_path):
    
    # This named file should be in the directory by the time this plotting fuction is called 
    fastq_file = fq_dir/"len_filter_reads.fq"
        
    passed_bases = count_fastq_bases(fastq_file)
    
    print(f'Calc n50 for plot')
    n50 = func_N50(lens_array)
    
    # conver to kb
    n50 = round(n50/1000, 1)
    total_data = round(passed_bases/1000000, 2)

    plot_path = results_path/f"{BARCODE}_read_length_distrabution_plot.png"
    
    print(f"Plottig {BARCODE} to: " + bcolors.HEADER + f"{plot_path}" + bcolors.ENDC)
    
    # plot the histogram
    plot = sns.displot(x=lens_array, 
                    weights = lens_array,
                    bins = 200, 
                    log_scale=(True,False), 
                    height=8,
                    aspect=2)

    plot.set(ylabel='bases', xlim=(800, max(lens_array)+5000))

    plot.figure.suptitle(f'''{BARCODE} Read length distribution\n N50: {n50}kb - Total data: {total_data}Mb''',
                  fontsize=24, fontdict={"weight": "bold"}, y=1.2)
    
    plot.savefig(plot_path)
    plt.close('all')
    return True


def run_seqkit_lenght_filter(fastq_file, read_len=900):
    '''
    Runs seqkit length filter on the fastq file.
    '''
    fastq_dir = fastq_file.parent
    BARCODE = fastq_dir.name
    print(f'\nRunning seqkit length filter for all read in sample: '+ bcolors.RED + f"{BARCODE}\n" + bcolors.ENDC)

    len_filt_file_path = fastq_dir/"len_filter_reads.fq"
    # the command, as a string, that will be used in a bash subprocess run the command
    len_filter_cmd = f"seqkit seq -g -m {read_len} {fastq_file} > {len_filt_file_path}"
    # span a subprocess and run the command
    sp = Popen(len_filter_cmd, shell=True, stdout=PIPE) # people dont like 'shell = true'
    # get the results back from the sp
    sp.communicate()
    # check the exit code
    if sp.returncode != 0:
        print(f'Error running seqkit length filter for sample: '+ bcolors.RED + f"{BARCODE}\n" + bcolors.ENDC)
        return False
    else:
        print(f'Seqkit length filter for sample ' + bcolors.RED + f"{BARCODE} " + bcolors.ENDC + 'complete\n')
        return len_filt_file_path



def kraken2_run(len_filtered_fastq: Path, BARCODE: str):
    '''
    Generates and runs the kraken2 call. Takes in the path to length filtered reads.
    Returns the path the the generated report 
    '''
    KREPORT_FILE_PATH=RESULTS_PATH/f"{BARCODE}_.kreport"
    OUTPUT_FILE_PATH=RESULTS_PATH/f"{BARCODE}_output.krk"
    CONFIDENCE='0.02'

    print(f'Running read classifier for sample: '+ bcolors.RED + f"{BARCODE}\n" + bcolors.ENDC)
    # this works
    run(['kraken2',
          '--db', KRAKEN2_DB_PATH,
          '--confidence', CONFIDENCE,
          '--report', KREPORT_FILE_PATH,
           '--output', OUTPUT_FILE_PATH,
           len_filtered_fastq],
           )
    
    return (OUTPUT_FILE_PATH, KREPORT_FILE_PATH)


def parse_kraken(BARCODE: str, kreport_path: Path) -> dict:
    '''
    Gets the top species hit from kraken2 for resfinder. 
    Output is a dict of the top three hits at the species level. 
    '''
    # set some parameters
    level="S"
    depth=3
    
    def extract_kreport(line, round_val=1 ):
        s = re.split("\t", re.sub("  ","",line.rstrip()))
        prcnt = str( round(float(s[0].lstrip()), round_val) )
        sp = s[len(s)-1]
        #return((sp, prcnt+"%"))
        #return(sp, prcnt+"%")
        return sp

    with open(kreport_path, "r") as f:
        #tax_dict = {}
        species = []
        for line in f:
        # extract all lines matching the required ID level
        #tax_level = line.split("\t")[3]
        #if tax_level == level: 
            if re.search("\t"+level, line): 
                species.append(extract_kreport( line, round_val=1 ))
            
        if species:
            if len(species) >= depth:
                tax_dict = {f'Taxon{i+1}':species[i] for i in range(depth)}
                tax_dict['Barcode'] = BARCODE
            else:
                tax_dict = {f'Taxon{i+1}':species[i] for i in range(len(species))}
                tax_dict['Barcode'] = BARCODE

            return tax_dict
        
        else:
            #quick fix for none empty kreports
            tax_dict = {'Barcode':BARCODE, 'Taxon1': 'None found'}

def write_classify_to_file(species_dict: dict) -> str: 
    '''
    Write the results of classificain to a single file: classification_results.csv. 
    Returns the top species for printing to screen.
    Needs a bit of formatting work.
    '''
    tax_csv_file_path = RESULTS_PATH/'classification_results.csv'
    tax_file_exists = tax_csv_file_path.is_file()
    
    with open(tax_csv_file_path, 'a') as tax_csv:
        header_names = ['Barcode', 'Taxon1', 'Taxon2', 'Taxon3']
        tax_writer = csv.DictWriter(tax_csv, fieldnames=header_names)
        
        if not tax_file_exists:
            tax_writer.writeheader()
        
        tax_writer.writerow(species_dict)

    top_species = species_dict['Taxon1']

    return top_species



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
        len_filtered_fastq = run_seqkit_lenght_filter(fastq_file)
        
        print("Filtered reads live at: " + bcolors.HEADER + f"{len_filtered_fastq}\n" + bcolors.ENDC)
        
        print(f'Calc length array for ' + bcolors.RED + f"{BARCODE}\n" + bcolors.ENDC)
        lens_array = get_lens_array(len_filtered_fastq)
        num_reads = len(lens_array)

        if num_reads < 1000:
            print(f'Skiping sample {BARCODE}, not enough reads\n')
            continue

        print(f'Passed reads: ' + bcolors.RED + f"{num_reads}\n" + bcolors.ENDC)
        

    
        # Do some plotting of the reads
        if not plot_length_dis_graph(fq_dir, BARCODE, lens_array, RESULTS_PATH):
            # need to clean up the temp files here
            os.remove(fastq_file)
            os.remove(len_filtered_fastq)
            continue

        # Run the classifer and unpack the tuple of Paths of the output files to vars
        KOUTPUT_PATH, KREPORT_PATH = kraken2_run(len_filtered_fastq, BARCODE)
        
        # parsing the k2 report to get top hits
        species_dict = parse_kraken(BARCODE, KREPORT_PATH)
        
        # writing the tophits to a file, probalby crash if there are no hits
        # needs attention
        top_species = write_classify_to_file(species_dict)

        print(bcolors.YELLOW + "\nTop classifiction hit: " + bcolors.BLUE + f"{top_species}\n" + bcolors.ENDC)


        # need to clean up the temp files here
        os.remove(fastq_file)
        os.remove(len_filtered_fastq)

    print(bcolors.YELLOW + "\nPOx_POC finished! Results are in: " + bcolors.HEADER + f"{RESULTS_PATH}" + bcolors.ENDC)
    print(bcolors.YELLOW + "\nThanks!" + bcolors.ENDC)

if __name__ == '__main__':
    main()
