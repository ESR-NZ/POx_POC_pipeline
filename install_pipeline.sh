#!/bin/bash

# Metagenomics Pipeline installer
# S Sturrock - ESR (modified by M Storey)
# 30/07/2021

# get the path of the repo
INSTALL_SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

echo "$INSTALL_SCRIPT_DIR"


# hard code for debugging (k database will go here)
#SSD_MOUNT="/path"

# get user input for database location
# uncomment below 
echo 'Enter the SSD mount path to download the kraken databse to:'
read -p '(e.g. /media/minit/xavierSSD ): ' SSD_MOUNT

if [ ! -d $SSD_MOUNT ]
then
    echo "Invalid location, please try again"
    exit 0
fi

#set up a bin dir to hold executibles 
BIN="$INSTALL_SCRIPT_DIR/bin"
[ ! -d $BIN ] && mkdir $BIN

DEPS="$INSTALL_SCRIPT_DIR/deps"
[ ! -d $DEPS ] && mkdir $DEPS

# Sort out some dependencies first

cd $DEPS
echo "Downloading seqkit static binary"
wget https://github.com/shenwei356/seqkit/releases/download/v2.1.0/seqkit_linux_arm64.tar.gz
tar -xvf seqkit_linux_arm64.tar.gz
mv seqkit $BIN
rm seqkit_linux_arm64.tar.gz
echo ""


# now the python dependencies
cd $INSTALL_SCRIPT_DIR

# following assumes conda is installed on the system, add this to README.md
echo "Setting up the conda environment"
# needed to use conda in a script
eval "$(command conda 'shell.bash' 'hook' 2> /dev/null)"

echo ""
echo "Installing python dependancies with conda"
echo ""
conda env update -q --file environment.yml

# Download and build kraken2
echo ""
echo "Download and build kraken2"
echo ""
cd $DEPS
git clone https://github.com/DerrickWood/kraken2.git
cd kraken2
./install_kraken2.sh $BIN

echo "^^^^ The above will be done automatically"
echo ""
# Need to set up the minikraken database
# put the mini-kraken2 database on the SSD.
K_DATABASE="${SSD_MOUNT}/kraken2_DBs"


if [ ! -f "${K_DATABASE}/minikraken2_v2_8GB_201904.tgz" ]; then
	echo "Kraken2 index database will be downloaded to: ${K_DATABASE}"
	# DL the databases 
	wget https://genome-idx.s3.amazonaws.com/kraken/minikraken2_v2_8GB_201904.tgz -P $K_DATABASE
	# unpack the .tgz
	cd $K_DATABASE
	tar -xvzf minikraken2_v2_8GB_201904.tgz
else
	echo "The Kraken database already exists. Skipping download"
fi

# symlink the run script to the repo bin dir
ln -s $INSTALL_SCRIPT_DIR/POX-POC_run.py $BIN/POX-POC_run.py


# prompt manually change the $PATH and set any environmental variable needed 
echo ""
echo "add the following to the end of your ~/.bashrc file" 
echo "export PATH=$BIN:\$PATH"
echo "export KRAKEN2_DB_PATH=${K_DATABASE}/minikraken2_v2_8GB_201904_UPDATE"

