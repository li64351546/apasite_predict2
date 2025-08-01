

python src/DaPars_Extract_Anno.py -b DATA/hg38_wholeGene_annotation.bed -s DATA/hg38_refseq_IDmapping.txt -o OUTPUT/hg38_3UTR_annotation.bed

python src/DaPars_Extract_Anno.py -b DATA/hg38_wholeGene_annotation.bed -s DATA/hg38_refseq_IDmapping.txt -o OUTPUT/hg38_3UTR_annotation.bed









0










[![Github Release](https://img.shields.io/badge/release-v2.1-brightgreen)](https://github.com/3UTR/DaPars2)
[![python Release](https://img.shields.io/badge/python-3.8-brightgreen)](https://www.python.org/downloads/)
[![numpy Release](https://img.shields.io/badge/numpy-1.22-brightgreen)](https://numpy.org/)
[![scipy Release](https://img.shields.io/badge/numpy-1.80-brightgreen)](https://scipy.org/)
[![R Release](https://img.shields.io/badge/R-3.6.3-brightgreen)](https://cran.r-project.org/)

# DaPars (v2.1)

Dynamics analysis of Alternative PolyAdenylation from multiple RNA-seq data

A [Full Documentations](https://github.com/3UTR/DaPars2/wiki) can be found in Wiki page. And a related 3'aQTL pipeline based on Dapars2 can be found [Here](https://github.com/3UTR/3aQTL-pipe).

## Introduction

The dynamic usage of the 3’untranslated region (3’UTR) resulting from alternative polyadenylation (APA) is emerging as a pervasive mechanism for regulating mRNA diversity, stability and translation. Though RNA-seq provides the whole-transcriptome information and a lot of tools for analyzing gene/isoform expression are available, very few tool focus on the analysis of 3’UTR from standard RNA-seq. DaPars v2 is the next generation of DaPars that directly infers the dynamic alternative polyadenylation (APA) usage by comparing standard RNA-seq from multiple samples. Given the annotated gene model, DaPars v2 can infer the de novo proximal APA sites as well as the long and short 3’UTR expression levels. Finally, the dynamic APA usages of each samples will be identified.

![Flowchart](https://farm8.staticflickr.com/7814/46170216185_6e5eb332fb.jpg) 

## Workflow

![Flowchart](https://farm8.staticflickr.com/65535/51154541918_8a63879ed1_k.jpg)


## Citation

*Please cite the following articles if you use DaPars2 in your research*:
* Feng X, Li L, Wagner EJ, Li W; TC3A: The Cancer 3′ UTR Atlas, Nucleic Acids Research, Volume 46, Issue D1, 4 January 2018, Pages D1027–D1030
* Li L^, Huang K^, Gao YP, Cui Y, Wang G, Nathan D, Li YM, Chen YE, Ji P, Peng F, William K, Wagner EJ, Li W. (2021) An atlas of alternative polyadenylation quantitative trait loci contributing to complex trait and disease heritability. Nature Genetics. doi: 10.1038/s41588-021-00864-5. 



## Contact

If you have any comments, suggestions, questions, bug reports, etc, feel free to contact Lei Li (lei.li.bioinfo@gmail.com). And PLEASE attach your command line and log messages if possible.


