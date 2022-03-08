import seaborn as sns
from matplotlib import pyplot as plt
from pox_poc import qc
from pox_poc.terminal_color import bcolors



def plot_length_dis_graph(qc_dict, plot_results_path):
    
    # ploting the length distribution
    
    BARCODE = qc_dict["BARCODE"]
    passed_bases = qc_dict["total_base_count"]
    lens_array = qc_dict["lens_array"]
    n50 = qc_dict["N50"]
    filter_length = qc_dict["filter_length"]

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
    