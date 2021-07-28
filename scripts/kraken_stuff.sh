#!/bin/bash

TAX_ID=1313

extracted_reads="Reads/${TAX_ID}_SUP_extracted_reads.fastq"
filtered_extracted_reads="Reads/${TAX_ID}_SUP_extracted_filtered_reads.fastq"

SUP_READS="/home/mstorey/Clinical_Seq/pleural_20210715/pleural_20210715/lib_1/20210715_0324_X3_FAP79707_f887d9d9/fastq_pass/barcode01_fastq_SUP/pass"

cat ${SUP_READS}/*.fastq > Reads/all_sup_reads.fq

READ_LEN=2000

filtlong --min_length $READ_LEN -t 300000000 Reads/all_sup_reads.fq > Reads/len_filter_kb_SUP_reads.fq
FILTERED_SUP_READS=Reads/len_filter_kb_SUP_reads.fq


module load kraken/2.0.7
kraken2 --db $KRAKEN2_DB_PATH --threads 24\
 --confidence 0.01\
 --report "Reports/len_fil_SUP_READS_krak_REPORT" --use-names\
 --output "Reports/len_fil_SUP_READS_krak__output" $FILTERED_SUP_READS



kraken2 --db $KRAKEN2_DB_PATH --threads 24\
 --confidence 0.02\
 --report "Reports/${TAX_ID}SUP_READS_krak_REPORT" --use-names\
 --output "Reports/${TAX_ID}SUP_READS_krak__output" $filtered_extracted_reads
module unload kraken/2.0.7
 
echo "generating krona plot: Reports/SUP_READS_krak.krona.html"
kreport2krona.py -r "Reports/len_fil_SUP_READS_krak_REPORT" -o "Reports/len_fil_SUP_READS_krak.krona.txt"


# make krona plot
source /opt/bioinf/anaconda3/anaconda3-5.0.0.1/bin/activate krona
ktImportText "Reports/len_fil_SUP_READS_krak.krona.txt" -o "Reports/len_fil_SUP_READS_krak.krona.html"
conda deactivate
