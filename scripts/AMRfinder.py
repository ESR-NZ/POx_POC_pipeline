#!/usr/bin/env python
# Created by jdeligt at 16.11.2021

# https://www.ncbi.nlm.nih.gov/pathogens/antimicrobial-resistance/AMRFinder/

"""Module for dealing with AMRfinder
- Run test suite
- Run amrfinder on a batch of samples
- Prepare output for dashborad with hAMRonization
"""
import hAMRonization

def run_tests():
    TESTDIR="/testdata/AMR/"
    
    # AMRFINDER
    # print a list of command-line options
    amrfinder --help

    # Download the latest AMRFinder plus database
    amrfinder -u
    # Protein AMRFinder with no genomic coordinates
    amrfinder -p {TESTDIR}test_prot.fa
    # Translated nucleotide AMRFinder (will not use HMMs)
    amrfinder -n {TESTDIR}test_dna.fa
    # Protein AMRFinder using GFF to get genomic coordinates and 'plus' genes
    amrfinder -p {TESTDIR}test_prot.fa -g {TESTDIR}test_prot.gff --plus
    # Protein AMRFinder with Escherichia protein point mutations
    amrfinder -p {TESTDIR}test_prot.fa -O Escherichia
    # Full AMRFinderPlus search combining results
    amrfinder -p {TESTDIR}test_prot.fa -g {TESTDIR}test_prot.gff -n {TESTDIR}test_dna.fa -O Escherichia --plus
    
    # hAMRonization

    
def run_amrfinder():
    # https://github.com/pha4ge/hAMRonization
    # amrfinder -n test_dna.fa
    
    
def parse_output():
    # https://github.com/pha4ge/hAMRonization
    # https://github.com/pha4ge/hAMRonization/blob/master/hAMRonization/AmrFinderPlusIO.py
    # metadata = {"analysis_software_version": "1.0.1", "reference_database_version": "2019-Jul-28"}
    # parsed_report = hAMRonization.parse("abricate_report.tsv", metadata, "abricate")
    # parsed_report.write('hAMRonized_abricate_report.tsv')
   