

import seaborn as sns
from matplotlib import pyplot as plt
from subprocess import Popen, PIPE, run

# terminal text color
class bcolors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'

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