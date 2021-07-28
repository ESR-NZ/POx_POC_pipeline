#!/usr/bin/env python
# coding: utf-8

from pathlib import Path
import os
from Bio import SeqIO
from subprocess import Popen, PIPE
import numpy as np
import seaborn as sns
from matplotlib import pyplot as plt

# This will be supplied by the API or as an arg by the user
minKnow_run_path = Path("/NGS/scratch/QC/NP_barcoded_test_data") # example minIon minKnow data path used for testing

# Will put results in the minKnow dir for now
results_path = minKnow_run_path/"Results"
if not results_path.is_dir():
    results_path.mkdir(exist_ok=True)

# Get a list of directories with fastqs in them, this works if multiplexed or not
def get_fastq_dirs(minKnow_run_path):
    '''
    Takes the top level run directory spawned by the sequencer run 
    as a Path object and returns an list of Path objects for the sub directories 
    that have fastqs in them
    '''
    fastq_dirs = [] 
    fq_glob_dirs = minKnow_run_path.rglob('*.fastq')
    for dirs in fq_glob_dirs:
        if dirs.parent not in fastq_dirs:
            fastq_dirs.append(dirs.parent)
        
    # remove unclassified from fastq_dirs
    for fq_dir in fastq_dirs:
        if fq_dir.name == "unclassified":
            fastq_dirs.remove(fq_dir)
    
    return fastq_dirs 


# concat reads for each "barcode" to single file for analysis
def concat_read_files(fq_dir: Path) -> Path:
    '''
    Takes in a Path object of a directory of fastq files and combines them
    into a singe file within that same directory. The function then returns
    the path to this new file. This uses the unix cat command.
    Could probably make this more parallel...   
    '''
    print(f'Concatenating read files in {fq_dir.name}') # print for debug
    all_reads = Path(f"{fq_dir / fq_dir.name}_all_reads.fq") 
    cat_cmd = f"cat {fq_dir}/*.fastq > {all_reads}"
    os.system(cat_cmd)
    return all_reads


# Function for data QC
def get_lens_array(fastq_file):
    '''
    Takes in a single fastq file and returns and list of the legths of each read
    in the file. Used to calc the N50 and histogram.
    Have identified that this can be done much faster with unix or Rust. 
    This will surfice for the draft script for now
    '''
    lens_array = [len(rec) for rec in SeqIO.parse(fastq_file, "fastq")]
    return lens_array


def func_N50(lens_array):
    '''
    Does what it says on the tin. Takes in the read lenths array and spits out the N50 stat
    Pretty slow tbh. Does the job for now but a work in progress. 
    '''
    unique = set(lens_array)
    n50_list = []
    for entry in unique:
        multi = lens_array.count(entry) * entry
        for i in range(multi):
            n50_list.append(entry)
    index = len(n50_list)/2
    ave = []
    if index % 2 == 0:
        first = n50_list[int(index)-1]
        second = n50_list[int(index)]
        ave.append(first)
        ave.append(second)
        n50 = np.mean(ave)
        return n50
    else:
        n50 = n50_list[int(index)-1]
        return n50


def count_fastq_bases(fastq_file):
    '''
    counts the number of bases sequenced in a fastq file
    '''
    cat_cms = f"cat {fastq_file} | paste - - - - | cut -f 2 | tr -d '\n' | wc -c"
    sp = Popen(cat_cms, shell=True, stdout=PIPE)
    bases = sp.communicate()[0]
    return int(bases.decode('ascii').rstrip())


def plot_length_dis_graph(fastq_file, results_path):
    barcode = fastq_file.name
    print(f'Calc length array for {barcode}')
    lens_array = get_lens_array(fastq_file)
    num_reads = len(lens_array)
    if num_reads < 1000:
        print(f'Skiping {barcode}, not enough reads')
        return 

    print(f'Calc passed bases for {barcode}')
    passed_bases = count_fastq_bases(fastq_file)
    
    print(f'Calc n50 for {barcode}')
    n50 = func_N50(lens_array)
    
    n50 = round(n50/1000, 1)
    total_data = round(passed_bases/1000000, 2)
        
    plot_dir  = Path("Plots")
    plot_dir.mkdir(exist_ok=True)

    plot_path = results_path/f"{barcode}_read_length_distrabution_plot.png"
    
    print(f"Plottig {barcode} to {plot_path}")
    
    plot = sns.displot(x=lens_array, log_scale=(True,False),height=8, aspect=2)

    plot.fig.suptitle(f'''{barcode} Read length distribution\n N50: {n50}kb - Total data: {total_data}Mb''',
                  fontsize=24, fontdict={"weight": "bold"}, y=1.2)
    
    plot.savefig(plot_path)
    plt.close('all')


def filtlong_run(fastq_file, read_len=1000):
    
    fastq_dir = fastq_file.parent
    len_filt_file_path = fastq_dir/"len_filter_reads.fq"
    
    filt_cmd = f'filtlong --min_length {read_len} {fastq_file} > {len_filt_file_path}'
    os.system(filt_cmd)
    
    return len_filt_file_path


# main func to run the script
def main():
    fastq_dirs = get_fastq_dirs(minKnow_run_path)
    all_reads_files = []
    
    for fq_dir in fastq_dirs:
        print(f'working on {fq_dir.name}')

        fastq_file = concat_read_files(fq_dir)
        all_reads_files.append(fastq_file.name)

        len_filtered_fastq = filtlong_run(fastq_file)

        print(f"Filtered reads live at {len_filtered_fastq}")
        
        plot_length_dis_graph(fastq_file, results_path)
 

if __name__ == '__main__':
    main()