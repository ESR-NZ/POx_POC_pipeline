# ResFinder

## install
`bash
conda install -y -c bioconda ncbi-amrfinderplus
conda activate
`
## update DB
`bash
amrfinder -u
`

## TEST data
`bash
curl -O https://raw.githubusercontent.com/ncbi/amr/master/test_dna.fa \
     -O https://raw.githubusercontent.com/ncbi/amr/master/test_prot.fa \
     -O https://raw.githubusercontent.com/ncbi/amr/master/test_prot.gff \
     -O https://raw.githubusercontent.com/ncbi/amr/master/test_both.expected \
     -O https://raw.githubusercontent.com/ncbi/amr/master/test_dna.expected \
     -O https://raw.githubusercontent.com/ncbi/amr/master/test_prot.expected 
`

## run TESTS
`bash
amrfinder --plus -n test_dna.fa -O Escherichia > test_dna.got
diff test_dna.expected test_dna.got
`
