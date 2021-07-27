# Demultiplex kraken output

Aim: demultiplex the output of Kraken to avoid loading the databases several times into memory which is slow and not scaleable

## Stuff

- Kraken is a fairly standard choice of software
- The output format that kraken uses is produced and used by many tools making it flexible 

kraken2 git repo: https://github.com/DerrickWood/kraken2

kraken2 docs: https://github.com/DerrickWood/kraken2/blob/master/docs/MANUAL.markdown#standard-kraken-output-format

kraken2 output format description: https://github.com/DerrickWood/kraken2/blob/master/docs/MANUAL.markdown#output-formats

## Have a look at Kraken output

- Output is a space delimited file

## Have a look at available demultiplexing tools

For each input DNA sample, a unique barcode is incorporated into the library of DNA molecules prepared for sequencing. Multiple barcoded DNA libraries can then be combined and sequenced simultaneously on the same flow cell. The resulting reads must then be demultiplexed: sorted into bins according to the barcode sequence

Tools for demultiplexing

- [qcat](https://github.com/nanoporetech/qcat) - used by the [nf-core/nanoseq](https://github.com/nf-core/nanoseq) pipeline, but qcat looks to be depreciated and not supported/recommended by Nanopore
- Nanopore now recommends the guppy basecaller (see the [README for qcat](https://github.com/nanoporetech/qcat#readme)) - that looks to be propriety software

Pretty sure the minion will run guppy on the fly during sequencing

- Could be useful: [jenniferlu717/KrakenTools](https://github.com/jenniferlu717/KrakenTools) - KrakenTools provides individual scripts to analyze Kraken/Kraken2/Bracken/KrakenUniq output files

Looks like you can extract fastq sequence files from kraken output using [extract_kraken_reads.py](https://github.com/jenniferlu717/KrakenTools#extract_kraken_reads.py)

## Try using [jenniferlu717/KrakenTools](https://github.com/jenniferlu717/KrakenTools)

Install

```bash
git clone https://github.com/jenniferlu717/KrakenTools.git
```

Have a look at the python version I have

```bash
python --version
```

My output:

```bash
Python 3.7.6
```

Try the [extract_kraken_reads.py script](https://github.com/jenniferlu717/KrakenTools#extract_kraken_readspy)

**We dropped the idea of demultiplexing after kraken since the loading of databases wasn't as slow as thought**
