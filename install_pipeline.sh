#!/bin/bash

# Metagenomics Pipeline installer
# S Sturrock - ESR
# 30/07/2021


PIPELINE=POX_POC_pipeline

# get user input for database location
echo 'Enter the SSD mount path to download the required databases to:'
read -p '(e.g. /media/minit/xavierSSD ): ' SSD_MOUNT

if [ ! -d $SSD_MOUNT ]
then
    echo "Invalid location, please try again"
    exit 0
fi

K_DATABASE="${SSD_MOUNT}/kraken2_DBs"
echo "Kraken2 index database will be downloaded to: ${K_DATABASE}"


# User can specify destination
if [ $# -lt 1 ]; then
	INSTALL_DIR=${PWD}/${PIPELINE}
else
	INSTALL_DIR=${1}/${PIPELINE}
fi

echo $INSTALL_DIR

# If the directory already exists, delete it
if [ -d $INSTALL_DIR ]; then
	rm -rf $INSTALL_DIR
fi

mkdir -p $INSTALL_DIR/bin
# Go into install directory and everything will be put in here
cd $INSTALL_DIR

# Download and build kraken2
git clone https://github.com/DerrickWood/kraken2.git
cd kraken2
./install_kraken2.sh $INSTALL_DIR/bin
# Create init.sh to set up path etc for user
echo "export PATH=${INSTALL_DIR}/bin:${PATH}" > $INSTALL_DIR/bin/init.sh
chmod +x $INSTALL_DIR/bin/init.sh
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

# Install R
mamba create -y -n r_env r-essentials r-base
mamba install -y -c conda-forge r-shinylp
mamba install -y -c conda-forge r-dt
conda install -y -c conda-forge r-flexdashboard
conda install -y -c conda-forge r-here
conda install -y -c conda-forge r-plotly
#mamba install -c conda-forge r-fontawesome
# recent version of fontawesome isn't available in conda
R -e "install.packages('fontawesome', repos='http://cran.rstudio.com/')"

# Install Python 3.9
PY3_VER=3.9
conda install -y python=${PY3_VER}
pip3 install -y seaborn

# Install filtlong
echo ""
cd $INSTALL_DIR
echo $INSTALL_DIR
PWD
echo ""

git clone https://github.com/rrwick/Filtlong.git
cd Filtlong
make -j # this seems to crash when run from the install script but completes ok from terminal.
mv bin/filtlong $INSTALL_DIR/bin


# Need to set up the minikraken database
cd $INSTALL_DIR
if [ ! -d $K_DATABASE/minikraken2_v2_8GB_201904.tgz ]
then
	# DL the databases 
	wget https://genome-idx.s3.amazonaws.com/kraken/minikraken2_v2_8GB_201904.tgz -P $K_DATABASE
	# unpack the .tgz
	cd $K_DATABASE
	tar -xvzf minikraken2_v2_8GB_201904.tgz 
fi

cd $INSTALL_DIR
