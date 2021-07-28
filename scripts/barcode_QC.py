#!/usr/bin/env python
# coding: utf-8


from pathlib import Path
import os
from Bio import SeqIO
from subprocess import Popen, PIPE
import numpy as np
import seaborn as sns
from matplotlib import pyplot as plt



def get_lens_array(fastq_file):
    
    lens_array = [len(rec) for rec in SeqIO.parse(fastq_file, "fastq")]
    return lens_array


def func_N50(lens_array):
   
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

def count_fastq_bases(reads_file):
    cat_cms = f"cat {reads_file} | paste - - - - | cut -f 2 | tr -d '\n' | wc -c"
    sp = Popen(cat_cms, shell=True, stdout=PIPE)
    bases = sp.communicate()[0]
    return int(bases.decode('ascii').rstrip())


# make length dis grapth
def plot_length_dis_graph(fastq_file):
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
    
    # shoud return the calulated data so we store it for later if we want...
    
    plot_dir  = Path("Plots")
    plot_dir.mkdir(exist_ok=True)
    plot_path = Path(f"Plots/{barcode}_Read_length_distrabution_plot.png")
    
    print(f"Plottig {barcode} to {plot_path}")
    
    plot = sns.displot(x=lens_array, log_scale=(True,False),height=8, aspect=2)

    plot.fig.suptitle(f'''{barcode} Read length distribution\n N50: {n50}kb - Total data: {total_data}Mb''',
                  fontsize=24, fontdict={"weight": "bold"}, y=1.2)
    
    plot.savefig(plot_path)
    plt.close('all')


def main():
    # path to barcode directories
    data_dir = Path("fastq_pass")
    barcode_dirs = [bc for bc in data_dir.iterdir() if bc.name.startswith('barcode')]



    # per barcode, concat the fastqs to a single file
    for barcode in barcode_dirs:
        
        passed_reads = Path(f"{barcode / barcode.name}_passed_reads.fq")
        
        if not passed_reads.is_file():
    
            cat_cms = f"cat {barcode}/*.fastq > {passed_reads}"
            print(f"Concat all passed reads for {barcode.name}")
            os.system(cat_cms)


    # get the paths to the concat read files for each bc
    fastq_allreads = []
    for barcode in barcode_dirs:
        files = [f for f in barcode.iterdir()]
        for file in files:
            if file.name.endswith('_passed_reads.fq'):
                fastq_allreads.append(file)

    # for loop the plots
    for fastq in fastq_allreads:
        plot_length_dis_graph(fastq)


if __name__ == "__main__":
    main()

#nees to run in a script. notebook cant call slurm...
# for fastq in fastq_allreads:
#     fastq_name = fastq.name
#     class_cmd = f'''
#     sbatch\
#     --output={classifer_dir}/{fastq_name}_slurm.out\
#      /home/mstorey/Fonterra_project_completion/Pipeline/Scripts/GridION_Classify.sh\
#      {fastq} {classifer_dir} {fastq_name}'''
    
#     print(f"Running classifier for {fastq_name}")
#     os.system(class_cmd)


