#!/bin/bash

# Metagenomics Pipeline installer
# S Sturrock - ESR
# 30/07/2021

# get the path of the repo
INSTALL_SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"


# hard code for debugging
SSD_MOUNT="/media/1tb_nvme"

# get user input for database location
# uncomment below 
#echo 'Enter the SSD mount path to install the pipeline to:'
#read -p '(e.g. /media/minit/xavierSSD ): ' SSD_MOUNT

if [ ! -d $SSD_MOUNT ]
then
    echo "Invalid location, please try again"
    exit 0
fi


CONDA_PATH=$(which conda)

echo $CONDA_PATH

exit 0


# Download and build kraken2
echo "Download and build kraken2"
echo ""
git clone https://github.com/DerrickWood/kraken2.git
cd kraken2
./install_kraken2.sh $INSTALL_DIR/bin


# put the database on the SSD outside the install dir to save DL'ing each time 
K_DATABASE="${SSD_MOUNT}/kraken2_DBs"
echo "Kraken2 index database will be downloaded to: ${K_DATABASE}"


# Create init.sh to set up path etc for user
touch $INSTALL_DIR/bin/init.sh
chmod +x $INSTALL_DIR/bin/init.sh

# Install filtlong
echo "Install filtlong"
echo ""
cd $INSTALL_DIR
git clone https://github.com/rrwick/Filtlong.git
cd Filtlong
make -j
mv bin/filtlong $INSTALL_DIR/bin
cd $INSTALL_DIR


# Set up miniconda
mkdir $INSTALL_DIR/miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh
bash Miniconda3-latest-Linux-aarch64.sh -b -f -p $INSTALL_DIR/miniconda
# Add miniconda to the init.sh
echo 'eval "$('$INSTALL_DIR'/miniconda/bin/conda shell.bash hook)"' >> $INSTALL_DIR/bin/init.sh

# Activate the conda env
eval "$(${INSTALL_DIR}/miniconda/bin/conda shell.bash hook)"
# Add channels
# conda config --add channels defaults
conda config --add channels bioconda
conda config --add channels conda-forge
# Mamba
conda install -y mamba -n base -c conda-forge

# recentrifuge install
mamba install -y -c bioconda recentrifuge
cd $INSTALL_DIR
git clone https://github.com/khyox/recentrifuge.git
cd recentrifuge
# Download NCBI node db
./retaxdump

# Install R, Shiny and flexdashboard
mamba install -y r-essentials r-base r-shinylp r-dt r-flexdashboard r-here r-plotly
# recent version of fontawesome isn't available in conda
R -e "install.packages('fontawesome', repos='http://cran.rstudio.com/')"

# copy the dashboaed app over to the install bin
cp -r $INSTALL_SCRIPT_DIR/dashboard $INSTALL_DIR/bin/dashboard
# Install seaborn
pip3 install seaborn



#Need to set up the minikraken database
if [ ! -f "${K_DATABASE}/minikraken2_v2_8GB_201904.tgz" ]; then
	# DL the databases 
	wget https://genome-idx.s3.amazonaws.com/kraken/minikraken2_v2_8GB_201904.tgz -P $K_DATABASE
	# unpack the .tgz
	cd $K_DATABASE
	tar -xvzf minikraken2_v2_8GB_201904.tgz 
fi

cd $INSTALL_DIR

# cp the run script and dashboard script to the pipeline bin dir so it will be in PATH
cp -r $INSTALL_SCRIPT_DIR/scripts $INSTALL_DIR/bin/scripts

#add stuff to path via init.script 
echo "export PATH=${INSTALL_DIR}/bin:${INSTALL_DIR}/bin/scripts:${INSTALL_DIR}/bin/dashboard:${INSTALL_DIR}/bin/dashboard/dashboard.Rmd:${PATH}" >> $INSTALL_DIR/bin/init.sh

# add some environmental vars (must be a better way to do this)
echo "export RCF_TAXDUMP=${INSTALL_DIR}/recentrifuge/taxdump" >> $INSTALL_DIR/bin/init.sh

echo "export KRAKEN2_DB_PATH=${K_DATABASE}/minikraken2_v2_8GB_201904_UPDATE" >> $INSTALL_DIR/bin/init.sh

# might need to add some conda stuff here for the launch script
echo "export CONDA_PATH=${INSTALL_DIR}/miniconda/etc/profile.d/conda.sh" >> $INSTALL_DIR/bin/init.sh

# this sucks, needs fixing
cat $INSTALL_DIR/bin/init.sh >> ~/.bashrc
