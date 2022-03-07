# POx_POC 

A work in progress. 

An installable environment and code for the Jetson Xaiver to analyse clinical bacterial isoaltes from nanopore sequencing data. This is a baseline minimum viable versions without the proposed results dashboard and other features. 

This analysis pipeline is designed to make read classificaion easy to run at a point-of-care setting. It will also produce some simple sequence data QC plots for each sample included in the run. The only expeced input for the programe is a barcoded ONT sequence run output directory. The program will search through the output directory to find each barcode and treat each one as a sample. Results will be printed to the screen and saved to a results directory too.        


## Install  

### Conda Note:
Requires `conda` to be installed on the system already. It uses `conda` to add a small number of pretty standard python packages (see `environment.yml`). These will, and can be, installed in the base conda environment, or which ever environment is activated at the time of install. As it is expected this is a dedicated sequencing device, the base conda environment will be the easiest for the end user. For future updates a dedicated environment my be used.  

To install:  

1) clone the git repo: `git clone https://github.com/ESR-NZ/POx_POC_pipeline.git`
2) move into the downloaded repo: `cd POx_POC_pipeline`
3) run the install script: `./install_pipeline.sh`
4) Enter the path to the mounted SSD on the system when prompted.  

The above commands will download and build the other software dependencies needed to run the analysis; namely [`seqkit `](https://bioinf.shenwei.me/seqkit/download/) and [`kraken2`](https://github.com/DerrickWood/kraken2). Acknowledgements to the authors of this excellent software. 

The first time the install script (`install_pipeline.sh`) is run it will also download the required kraken2 database to the SSD.  
You will need to add the created `bin` directory to your path, as well as, an environent variable (`KRAKEN2_DB_PATH`) so the run script knows where to find the kraken2 database. There are instructions to copy/paste the required lines to your `.bascrc` file shown at the end of the install process, so watch out for those.   

## Running the analysis  

Once installed, the "pipeline" can be run with the command:  
`POX-POC_run.py <path/to/run_directory>`  

Results can be found in:   
`path/to/run_directory/POx_POC_results`  

This can be run during the sequencing experiment if required to analyse the data generated upto that point.  


## Output

to write...
