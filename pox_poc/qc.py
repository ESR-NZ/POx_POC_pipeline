import gzip
from Bio import SeqIO
from pathlib import Path
from subprocess import Popen, PIPE
from pox_poc.terminal_color import bcolors


# Functions for data QC and to support the plotting

def is_gz_file(file_path: Path) -> bool:
    '''
    dirty trick to check for gzipped files based on magic number first 2 bites
    '''
    with open(file_path, 'rb') as f:
        is_gzip = f.read(2) == b'\x1f\x8b'

        return is_gzip


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