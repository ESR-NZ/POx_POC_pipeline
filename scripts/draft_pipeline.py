#!/usr/bin/env python
# coding: utf-8

from pathlib import Path
import os
from Bio import SeqIO

# This will be supplied by the API or as an arg by the user
minKnow_run_path = Path("/NGS/scratch/QC/NP_barcoded_test_data") # example minIon minKnow data path used for testing

# Will put results in the minKnow dir for now
results_path = minKnow_run_path/"Results"

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


def main():
    fastq_dirs = get_fastq_dirs(minKnow_run_path)
    for i in fastq_dirs:
        print(i.name)


if __name__ == '__main__':
    main()