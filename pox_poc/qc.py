import gzip
from Bio import SeqIO
from pathlib import Path
from subprocess import Popen, PIPE, run
from pox_poc.terminal_color import bcolors
import os

# Functions for data QC and to support the plotting

def is_gz_file(file_path: Path) -> bool:
    '''
    dirty trick to check for gzipped files based on magic number first 2 bites
    '''
    with open(file_path, 'rb') as f:
        is_gzip = f.read(2) == b'\x1f\x8b'

        return is_gzip


def count_fastq_bases(fastq_file):
    '''
    counts the number of bases sequenced in a fastq file
    '''
    # the command, as a string, that will be used in a bash subprocess to do the calculation
    if is_gz_file(fastq_file):
        cat_cmd = f"zcat {fastq_file} | paste - - - - | cut -f 2 | tr -d '\n' | wc -c"
    else:
        cat_cmd = f"cat {fastq_file} | paste - - - - | cut -f 2 | tr -d '\n' | wc -c"
    # spawn a subprocess and run the command
    sp = Popen(cat_cmd, shell=True, stdout=PIPE) # people dont like 'shell = true'
    # get the results back from the sp
    bases = sp.communicate()[0]
    
    return int(bases.decode('ascii').rstrip())


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

    len_filt_file_path = fastq_dir/f"{BARCODE}_len_filter_reads.fq"
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