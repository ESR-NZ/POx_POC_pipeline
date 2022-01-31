import seaborn as sns
from matplotlib import pyplot as plt
from subprocess import Popen, PIPE, run
from pox_poc import qc
from pox_poc.terminal_color import bcolors



def plot_length_dis_graph(fq_dir, BARCODE, lens_array, results_path):
    
    # This named file should be in the directory by the time this plotting fuction is called 
    fastq_file = fq_dir/f"{BARCODE}_len_filter_reads.fq"
        
    passed_bases = qc.count_fastq_bases(fastq_file)
    
    print(f'Calc n50 for plot')
    n50 = qc.func_N50(lens_array)
    
    # conver to kb/mb
    n50 = round(n50/1000, 1)
    total_data = round(passed_bases/1000000, 2)

    plot_path = results_path/f"{BARCODE}_read_length_distrabution_plot.png"
    
    print(f"Plottig {BARCODE} to: " + bcolors.HEADER + f"{plot_path}" + bcolors.ENDC)
    
    # plot the histogram
    plot = sns.displot(x=lens_array, 
                    weights = lens_array,
                    bins = 200,
                    kde = True,
                    log_scale=(True,False), 
                    height=8,
                    aspect=2)

    plot.set(ylabel='bases', xlim=(800, max(lens_array)+5000))

    plot.figure.suptitle(f'''{BARCODE} Read length distribution\n N50: {n50}kb - Total data: {total_data}Mb''',
                  fontsize=24, fontdict={"weight": "bold"}, y=1.2)
    
    plot.savefig(plot_path)
    plt.close('all')
    return True