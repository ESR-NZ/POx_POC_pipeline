import gzip
from Bio import SeqIO
from pathlib import Path
from subprocess import Popen, PIPE, run
from pox_poc.terminal_color import bcolors
import os
import gzip

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


def run_seqkit_lenght_filter(fastq_file, BARCODE, COMBINED_FASTQ_DIR, read_len=1000):
    '''
    Runs seqkit length filter on the fastq file and return the filtered file path.
    '''
    
    print(f'\nRunning seqkit length filter for all reads in sample: '+ bcolors.RED + f"{BARCODE}\n" + bcolors.ENDC)

    # create the output file name
    len_filt_file_path = COMBINED_FASTQ_DIR/f"{BARCODE}_all_reads_lenght_filtered.fastq.gz"
    # the command, as a string, that will be used in a bash subprocess run the command
    len_filter_cmd = f"seqkit seq -g -m {read_len} -o {len_filt_file_path} {fastq_file}"
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
def concat_read_files(fq_dir: Path, COMBINED_FASTQ_DIR: Path) -> Path:
    '''
    Takes in a Path object of a directory of fastq.(gz) files and combines them
    into a singe file in a Combind_fastq dir. The function then returns
    the path to this new file. This uses the unix cat command.
    Could probably make this more parallel...   
    '''
    # initiualize the combined fastq file path
    all_reads = Path(COMBINED_FASTQ_DIR / f"{fq_dir.name}_all_reads") 
    
    # remove any tmp files from previous crashed runs
    # this works but is ugly, needs attention
    if all_reads.with_suffix('.fastq').is_file():
        os.remove(all_reads.with_suffix('.fastq'))
    if all_reads.with_suffix('.fastq.gz').is_file():
        os.remove(all_reads.with_suffix('.fastq.gz'))
    
    # get a list of all fastq type files in the directory using glob
    fq_files = list(fq_dir.glob('*.fastq*'))

    # seperate the gz and non gz files
    # needs to be a list of strings so the .join method in the cat_cmd fstring works
    fastq_gz_files = [str(f) for f in fq_files if is_gz_file(f)]
    fastq_files = [str(f) for f in fq_files if not is_gz_file(f)]

    # this will hold the temp files that are created by the cat commands to be combined later
    temp_file_list = []

    # combine the gz files to a temp file
    if len(fastq_gz_files) > 0:
        cat_cmd = f"cat {' '.join(fastq_gz_files)} > {all_reads.with_suffix('.temp_1.fastq.gz')}"
        sp = Popen(cat_cmd, shell=True, stdout=PIPE)
        sp.communicate()
        if sp.returncode != 0:
            print(f'Error running fastq.gz cat command for sample: '+ bcolors.RED + f"{fq_dir.name}\n" + bcolors.ENDC)
            return False
        else:
            # add the temp file to temp file list
            temp_file_list.append(all_reads.with_suffix('.temp_1.fastq.gz'))
    
    # combine the non gz files to a temp file, gzip it and then add it to the temp file list 
    if len(fastq_files) > 0:
        cat_cmd = f"cat {' '.join(fastq_files)} > {all_reads.with_suffix('.temp_2.fastq')}"
        sp = Popen(cat_cmd, shell=True, stdout=PIPE)
        sp.communicate()
        if sp.returncode != 0:
            print(f'Error running fastq cat command for sample: '+ bcolors.RED + f"{fq_dir.name}\n" + bcolors.ENDC)
            return False
        else:
            gzip_cmd = f"gzip {all_reads.with_suffix('.temp_2.fastq')}"
            run(gzip_cmd, shell=True, stdout=PIPE)
            #add the temp file to temp file list
            temp_file_list.append(all_reads.with_suffix('.temp_2.fastq.gz'))


    # concat the temp files to the combined fastq.gz file for final output
    cat_cmd = f"cat {' '.join([str(t) for t in temp_file_list])} > {all_reads.with_suffix('.fastq.gz')}"
    sp = Popen(cat_cmd, shell=True, stdout=PIPE)
    sp.communicate()
    if sp.returncode != 0:
        print(f'Error running cat command for sample: '+ bcolors.RED + f"{fq_dir.name}\n" + bcolors.ENDC)
        return False
    else:
        # remove the temp files
        for f in temp_file_list:
            os.remove(f)
        # return the path to the combined fastq file
        return all_reads.with_suffix('.fastq.gz')   

    

    
    
  

