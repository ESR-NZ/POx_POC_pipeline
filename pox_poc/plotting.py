import seaborn as sns
from matplotlib import pyplot as plt
from subprocess import Popen, PIPE, run
from pox_poc import qc
from pox_poc.terminal_color import bcolors



def plot_length_dis_graph(fastq_file, BARCODE, filter_length, lens_array, plot_results_path):
    
    # plot the length distribution
    
    passed_bases = qc.count_fastq_bases(fastq_file)
    
    print(f'Calc n50 for plot')
    n50 = qc.func_N50(lens_array)
    
    # conver to kb/mb
    n50 = round(n50/1000, 1)
    total_data = round(passed_bases/1000000, 2)

    plot_path = plot_results_path/f"{BARCODE}_read_length_distrabution_plot.png"
    
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

    plot.figure.suptitle(f'''{BARCODE} Read length distribution\n N50: {n50}kb - Total data (reads > {filter_length}bp): {total_data}Mb''',
                  fontsize=24, fontdict={"weight": "bold"}, y=1.2)
    
    plot.savefig(plot_path)
    plt.close('all')
    