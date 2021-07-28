# notes on Nvidia Jetson Xavier set up and testing

Running notes documenting the set up and testing of various components of the sprint.

## jtop

```sh
# install jtop for monitoring system
sudo apt update 
sudo apt install python3-pip 
sudo -H pip3 install -U jetson-stats
sudo systemctl restart jetson_stats.service
source .bashrc 
```

## docker

```sh
# had some docker permission issues
sudo chown "$USER":"$USER" /home/"$USER"/.docker -R
sudo chmod g+rwx "/home/$USER/.docker" -R
```

## kraken2 testing

### Zymo mock community test data

```sh
# docker kraken2 - zymo mock community data
docker run -ti \
  -v /data/databases/:/mnt/databases/ \
  -v /data/testdata/:/mnt/testdata/ \
  -v /data/output/:/mnt/output/ \
  nvcr.io/nvidia/clara-agx/agx-metagenomics-classify-reference classify \
  -H /mnt/databases/minikraken2_v1_8GB/hash.k2d \
  -t /mnt/databases/minikraken2_v1_8GB/taxo.k2d \
  -o /mnt/databases/minikraken2_v1_8GB/opts.k2d \
  /mnt/testdata/zymo_combined_shortrun.fastq \
  -O /mnt/output/zymo_mockcommunity_kr2_output \
  -R /mnt/output/zymo_mockcommunity_kr2_report \
  -n
Loading database information... done.
128012 sequences (213.35 Mbp) processed in 14.326s (536.1 Kseq/m, 893.55 Mbp/m).
  119520 sequences classified (93.37%)
  8492 sequences unclassified (6.63%)
```

#### --memory-mapping

Using the `-M` (`--memory-mapping`) flag to not load the database directly into RAM. This saves RAM but takes longer. Let's see how much longer:

```sh
# adding the -M (--memory-mapping) parameter to not use RAM
docker run -ti \
  -v /data/databases/:/mnt/databases/ \
  -v /data/testdata/:/mnt/testdata/ \
  -v /data/output/:/mnt/output/ \
  nvcr.io/nvidia/clara-agx/agx-metagenomics-classify-reference classify \
  -H /mnt/databases/minikraken2_v1_8GB/hash.k2d \
  -t /mnt/databases/minikraken2_v1_8GB/taxo.k2d \
  -o /mnt/databases/minikraken2_v1_8GB/opts.k2d \
  /mnt/testdata/zymo_combined_shortrun.fastq \
  -O /mnt/output/zymo_mockcommunity_kr2_output \
  -R /mnt/output/zymo_mockcommunity_kr2_report \
  -n
Loading database information... done.
128012 sequences (213.35 Mbp) processed in 17.558s (437.4 Kseq/m, 729.07 Mbp/m).
  119520 sequences classified (93.37%)
  8492 sequences unclassified (6.63%)
```

That's actually not too bad (even though it's is a small data set), it takes **3 seconds** longer with `--memory-mapping`. This isn't really a problem for the 16Gb/32Gb Xavier AGX units, but it means that the 8Gb NX units will actually be able to run classification, which is great!

### barcoded test data (bacterial isolates)

```sh
# docker kraken2 - barcode data
docker run -ti \
  -v /data/databases/:/mnt/databases/ \
  -v /data/testdata/:/mnt/testdata/ \
  -v /data/output/:/mnt/output/ \
  nvcr.io/nvidia/clara-agx/agx-metagenomics-classify-reference classify \
  -H /mnt/databases/minikraken2_v1_8GB/hash.k2d \
  -t /mnt/databases/minikraken2_v1_8GB/taxo.k2d \
  -o /mnt/databases/minikraken2_v1_8GB/opts.k2d \
  /mnt/testdata/barcoded/fastq_pass/barcode26/barcode26_1k.fq \
  -O /mnt/output/barcode26_kr2_output \
  -R /mnt/output/barcode26_kr2_report \
  -n
Loading database information... done.
4912 sequences (40.22 Mbp) processed in 2.777s (106.1 Kseq/m, 868.85 Mbp/m).
  4910 sequences classified (99.96%)
  2 sequences unclassified (0.04%)
```

```sh
# Matt's klass_parse.py script running on the kraken2 report file 
python3 klass_parse.py 
{​'Taxon1': ('Bifidobacterium animalis', '99.9%'), 'Taxon2': ('Bifidobacterium animalis subsp. animalis', '28.0%'), 'Taxon3': ('Bifidobacterium animalis subsp. animalis ATCC 25527', '7.0%')}​
```

## miniconda

This used to be tricky on ARM but now miniconda have dedicated ARM builds ([link](https://repo.anaconda.com/miniconda/)). I've grabbed the latest build ([link](https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh)).

```sh
# set up conda
mkdir miniconda
cd miniconda/
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh
chmod +x Miniconda3-latest-Linux-aarch64.sh 
./Miniconda3-latest-Linux-aarch64.sh 
source ~/.bashrc
```

#### channels

```sh
conda config --add channels defaults
conda config --add channels bioconda
conda config --add channels conda-forge
```

#### mamba

```sh
conda install mamba -n base -c conda-forge
```

#### recentrifuge

```sh
mamba install -c bioconda recentrifuge
```

Probably should have created an env here... oh well! Looks like it is working:

```sh
rcf --version

=-= /xavier_ssd/miniconda3/bin/rcf =-= v1.3.3 - May 2021 =-= by Jose Manuel Martí =-=

rcf version 1.3.3 released in May 2021
```

```sh
git clone https://github.com/khyox/recentrifuge.git
cd recentrifuge
./retaxdump     # download NCBI node db
# -n /xavier_ssd/gitrepo/recentrifuge/taxdump       # use this dir as -n flag
```

```sh
rcf -n /xavier_ssd/gitrepo/recentrifuge/taxdump -k zymo_mockcommunity_kr2_output.krk

=-= /xavier_ssd/miniconda3/bin/rcf =-= v1.3.3 - May 2021 =-= by Jose Manuel Martí =-=

Loading NCBI nodes... OK! 
Loading NCBI names... OK! 
Building dict of parent to children taxa... OK! 

Please, wait, processing files in parallel...

Loading output file zymo_mockcommunity_kr2_output.krk... OK!
  Seqs read: 128_011	[213.35 Mnt]
  Seqs clas: 119_519	(6.63% unclassified)
  Seqs pass: 119_519	(0.00% rejected)
  Scores SHEL: min = 35.0, max = 1067.0, avr = 79.0
  Coverage(%): min = 0.0, max = 25.5, avr = 2.8
  Read length: min = 136 nt, max = 19.18 knt, avr = 1.72 knt
  TaxIds: by classifier = 1009, by filter = 1009
Building from raw data with mintaxa = 5 ... 
  Check for more seqs lost ([in/ex]clude affects)... 
  Info: 1091 additional seqs discarded (0.913% of accepted)

  Warning! 4 orphan taxids (rerun with --debug for details)
zymo_mockcommunity_kr2_output sample OK!
Load elapsed time: 11.1 sec


Building the taxonomy multiple tree... OK!
Generating final plot (zymo_mockcommunity_kr2_output.krk.rcf.html)... OK!
Generating Excel full summary (zymo_mockcommunity_kr2_output.krk.rcf.xlsx)... OK!
Total elapsed time: 00:00:42
```

![recentrifuge_plot](images/recentrifuge_zymodata.png)

```sh
rcf -n /xavier_ssd/gitrepo/recentrifuge/taxdump -k barcode26_kr2_output.krk 

=-= /xavier_ssd/miniconda3/bin/rcf =-= v1.3.3 - May 2021 =-= by Jose Manuel Martí =-=

Loading NCBI nodes... OK! 
Loading NCBI names... OK! 
Building dict of parent to children taxa... OK! 

Please, wait, processing files in parallel...

Loading output file barcode26_kr2_output.krk... OK!
  Seqs read: 4_911	[40.21 Mnt]
  Seqs clas: 4_909	(0.04% unclassified)
  Seqs pass: 4_909	(0.00% rejected)
  Scores SHEL: min = 35.0, max = 4729.0, avr = 322.4
  Coverage(%): min = 0.0, max = 17.1, avr = 5.3
  Read length: min = 1000 nt, max = 76.79 knt, avr = 8.19 knt
  TaxIds: by classifier = 16, by filter = 16
Building from raw data with mintaxa = 4 ... 
  Check for more seqs lost ([in/ex]clude affects)... OK!
barcode26_kr2_output sample OK!
Load elapsed time: 2.65 sec


Building the taxonomy multiple tree... OK!
Generating final plot (barcode26_kr2_output.krk.rcf.html)... OK!
Generating Excel full summary (barcode26_kr2_output.krk.rcf.xlsx)... OK!
Total elapsed time: 00:00:32
```

##### 'grouped' analysis

It turns out that `recentrifuge` has the ability to detect and process multiple kraken2 outputs in a dir. The only requirement is that the kraken2 outputs finish with the `.krk` file extension. Then the following can be run:

```sh
rcf -n /data/gitrepos/recentrifuge/taxdump -k ./ -o recentrifuge_group_analysis.html -e CSV
```

This produces something like the following:

```sh
-rw-rw-r-- 1 minit minit 661K Jul 28 15:44 recentrifuge_group_analysis.html
-rw-rw-r-- 1 minit minit 2.0K Jul 28 15:44 recentrifuge_group_analysis.stat.csv
-rw-rw-r-- 1 minit minit 118K Jul 28 15:44 recentrifuge_group_analysis.data.csv
```

So a single set of 'data' and html that contains all samples in a given 'run'. Neat!

## other python packages required

The current draft pipeline ans associated scripts depend on the below (as well as anything previously mentioned):

```sh
# these are the current python deps i have for the run script
from pathlib import Path
import os
from Bio import SeqIO
from subprocess import Popen, PIPE
import numpy as np
import seaborn as sns
from matplotlib import pyplot as plt
```

Might be useful to have a `requirements.txt`?

```sh
pathlib
Bio
subprocess
numpy
pandas
seaborn
matplotlib
pprint
```

## filtlong

Grab filtlong from the repo, make and install (add to path).

```sh
# clone and make
git clone https://github.com/rrwick/Filtlong.git
cd Filtlong
make -j
bin/filtlong -h
```

```sh
# add to path
sudo cp bin/filtlong /usr/local/bin

# check
filtlong --version
Filtlong v0.2.1
```

## MinKNOW API

With the MinKNOW API we can poll data in real-time. You can also set up and control runs as well.

Get the repo and install the API:

```sh
# grab repo
git clone https://github.com/nanoporetech/minknow_api.git
cd minknow_api

# Install minknow_api
pip install minknow_api
```

Now we can test it:

```sh
# Verify API is installed correctly (from a checkout of this repository):
python ./python/examples/list_sequencing_positions.py --host localhost --port 9501

Available sequencing positions on localhost:9501:
MN34702: running
  secure: 8001
  insecure: 8000
```

Cool! The above has identified the device correctly, and that it is running.

