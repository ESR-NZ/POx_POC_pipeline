# do the concat with unix cat command
    print(f'Concatenating all read files to {all_reads.name}.fastq.gz') # print for debug
    print([f for f in fq_dir.glob('*.fastq.*')]) # print for debug
    for file in fq_dir.iterdir():
        print(f"\t{file.name}")
    
        
        if is_gz_file(file):
            print(f'\t{file.name} is gzipped')
            cat_cmd = f"zcat {file} >> {all_reads.with_suffix('.fastq.gz')}"
        else:
            print(f'\t{file.name} is not gzipped')
            cat_cmd = f"cat {file} | gzip >> {all_reads.with_suffix('.fastq.gz')}"
        
        print(f"\t{cat_cmd}")
        sp = Popen(cat_cmd, shell=True, stdout=PIPE)
        sp.communicate()
        
        if sp.returncode != 0:
            print(f'Error concatenating files for sample: '+ bcolors.RED + f"{fq_dir.name}\n" + bcolors.ENDC)
            return False
        else:
            print(f'Concatenation of all read files to {all_reads.name}.fastq.gz complete\n')
            return all_reads.with_suffix('.fastq.gz')