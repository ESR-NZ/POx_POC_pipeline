#!/usr/bin/env python

from pathlib import Path
from pox_poc import qc
import os

# hardcode a test path

run_path = Path("/media/1tb_nvme/Test_sets/barcode01")

# count the number of fastq.gz files in the supplied run_path
fastq_files_gz = list(run_path.glob("*.fastq.gz"))
print(f"Found {len(fastq_files_gz)} fastq.gz files in {run_path}\n")


# count the number of fastq.gz files in the supplied run_path
fastq_files = list(run_path.glob("*.fastq"))
print(f"Found {len(fastq_files)} fastq files in {run_path}\n")

def count_number_of_reads(fastq_file):
    """Count the number of reads in the supplied fastq.gz files"""
    # count the number of reads in the supplied fastq.gz files
    len_array = qc.get_lens_array(fastq_file)
    num_reads = len(len_array)
    return num_reads

# count the number of reads in each fastq file and print the total
gz_read_count = 0
for fastq in fastq_files_gz:
    number_of_reads = count_number_of_reads(fastq)
    gz_read_count += number_of_reads

print(f"Total number of reads in raw gz files: {gz_read_count}\n")

# count the number of reads in each fastq file and print the total
fq_read_count = 0
for fastq in fastq_files:
    number_of_reads = count_number_of_reads(fastq)
    fq_read_count += number_of_reads


print(f"Total number of reads in raw fastq files: {fq_read_count}\n")

total_reads = gz_read_count + fq_read_count
print(f"Total number of reads in raw files: {total_reads}\n")

# make a qc_testing out directory
qc_testing_dir = Path(run_path.parent, "qc_testing")
qc_testing_dir.mkdir(exist_ok=True)

# run the concat_read_files function
combined_reads = qc.concat_read_files(run_path, qc_testing_dir)

# count the number of reads in combined_reads
combined_number_of_reads = count_number_of_reads(combined_reads)
print(f"\nTotal number of reads in combined: {combined_number_of_reads}")

# sequence length filter combined_reads
len_filtered_reads = qc.run_seqkit_lenght_filter(combined_reads, "barcode01", qc_testing_dir, 0)

# count the number of reads in the len_filtered_reads file
len_filtered_reads_count = count_number_of_reads(len_filtered_reads)
print(f"Total number of reads in len_filtered_reads: {len_filtered_reads_count}")

