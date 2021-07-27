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

## miniconda

```sh
# set up conda
mkdir miniconda
cd miniconda/
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh
chmod +x Miniconda3-latest-Linux-aarch64.sh 
./Miniconda3-latest-Linux-aarch64.sh 
```

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