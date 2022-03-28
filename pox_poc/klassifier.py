from pathlib import Path
from subprocess import run
from pox_poc.terminal_color import bcolors
import os
import re
import csv

KRAKEN2_DB_PATH=os.environ.get('KRAKEN2_DB_PATH')

def kraken2_run(len_filtered_fastq: Path, BARCODE: str, KREPORT_DIR: Path) -> dict:
    '''
    Generates and runs the kraken2 call. Takes in the path to length filtered reads.
    Returns the path the the generated report 
    '''
    KREPORT_FILE_PATH=KREPORT_DIR/f"{BARCODE}_.kreport"
    OUTPUT_FILE_PATH=KREPORT_DIR/f"{BARCODE}_output.krk"
    CONFIDENCE='0.02'

    print(f'Running read classifier for sample: '+ bcolors.RED + f"{BARCODE}\n" + bcolors.ENDC)
    # this works
    run(['kraken2',
          '--db', KRAKEN2_DB_PATH,
          '--confidence', CONFIDENCE,
          '--report', KREPORT_FILE_PATH,
           '--output', OUTPUT_FILE_PATH,
           len_filtered_fastq],
           )

    return (KREPORT_FILE_PATH, OUTPUT_FILE_PATH)


def parse_kraken(BARCODE: str, kreport_path: Path) -> dict:
    '''
    Gets the top species hit from kraken2 for resfinder. 
    Output is a dict of the top three hits at the species level. 
    '''
    # set some parameters
    level="S"
    depth=3
    
    def extract_kreport(line, round_val=1 ):
        s = re.split("\t", re.sub("  ","",line.rstrip()))
        prcnt = str( round(float(s[0].lstrip()), round_val) )
        sp = s[len(s)-1]
        #return((sp, prcnt+"%"))
        return f'{sp} - {prcnt}%'
        #return sp

    with open(kreport_path, "r") as f:
        #tax_dict = {}
        species = []
        for line in f:
        # extract all lines matching the required ID level
        #tax_level = line.split("\t")[3]
        #if tax_level == level: 
            if re.search("\t"+level, line): 
                species.append(extract_kreport( line, round_val=1 ))

        # get the top three hits
        
        if species:
            if len(species) >= depth:
                tax_dict = {f' Taxon{i+1}':species[i] for i in range(depth)}
                tax_dict['Barcode'] = BARCODE
            else:
                tax_dict = {f' Taxon{i+1}':species[i] for i in range(len(species))}
                for i in range(len(species), depth):
                    tax_dict[f' Taxon{i+1}'] = "No hits"
                tax_dict['Barcode'] = BARCODE

            return tax_dict

        else:
            return {'Barcode':BARCODE, ' Taxon1':'No hits', ' Taxon2':'No hits', ' Taxon3':'No hits'}
       

def write_update_dict_to_file(updated_dict: dict, RESULTS_PATH) -> str: 
    '''
    Write the results of classificain to a single file: classification_results.csv. 
    Returns the top species for printing to screen.
   
    Also now writes the qc data to the file too. Species dict is updated with qc_dict in main()
    proior calling this fuctions.

    '''
    tax_csv_file_path = RESULTS_PATH/'classification_results.csv'
    tax_file_exists = tax_csv_file_path.is_file()
    
    with open(tax_csv_file_path, 'a') as tax_csv:
        header_names = ['Barcode', ' Taxon1', ' Taxon2', ' Taxon3', ' N50 (kb)', ' number_of_reads', ' total_bases (Mb)']
        tax_writer = csv.DictWriter(tax_csv, fieldnames=header_names)
        
        if not tax_file_exists:
            tax_writer.writeheader()
        # better to format the header names here?

        # trim the dict to only the header names we want to write
        dict_to_write = {k:updated_dict[k] for k in header_names}
    
        tax_writer.writerow(dict_to_write)    

    top_species = dict_to_write[' Taxon1']

    return top_species