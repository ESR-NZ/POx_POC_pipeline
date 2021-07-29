#!/usr/bin/env python

#from os import name
#import pandas as pd
from pathlib import Path
import re
import fileinput

# path_to_example_kreport = Path("./Results/barcode02_.kreport")
path_to_example_kreport = input()   # capture file input from stdin

# global params
level="S"
depth=3


def extract_kreport(line, round_val=1 ):
    s = re.split("\t", re.sub("  ","",line.rstrip()))
    prcnt = str( round(float(s[0].lstrip()), round_val) )
    sp = s[len(s)-1]
    return((sp, prcnt+"%"))



def parse_kreport_species(kreport):
    with open(kreport, "r") as f:
        tax_dict = {}
        species = []
        for line in f:
            # extract all lines matching the required ID level
            #tax_level = line.split("\t")[3]
            #if tax_level == level: 
            if re.search("\t"+level, line): 
                species.append(extract_kreport( line, round_val=1 ))
                
        if len(species) >= depth:
            tax_dict = {f'Taxon{i+1}':species[i] for i in range(depth)}
        else:
            tax_dict = {f'Taxon{i+1}':species[i] for i in range(len(species))}
        
    return tax_dict




def main():
    print(parse_kreport_species(path_to_example_kreport))

if __name__ == "__main__":
    main()
