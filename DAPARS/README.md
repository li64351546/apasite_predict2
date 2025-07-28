


python src/DaPars_Extract_Anno.py -b DATA/hg19_refseq_extracted_3UTR.bed -s /home/li/桌面/PROJECT6/apasite_predict2/DAPARS2/DATA/hg38_refseq_IDmapping.txt  -o DATA/123.bed

python DaPars_Extract_Anno.py -b INPUT BED FILE -s ANNOTATION FILE -o OUTPUT BED FILE






python src/DaPars_main.py DATA/DaPars_test_data_configure.txt

python DaPars_main.py CONFIGURATION FILE














DAPARS/src/DaPars_Extract_Anno.py

[**Full Documentations**](http://xiazlab.org/dapars_tutorial/html/DaPars.html)
Description
-----
The dynamic usage of the 3’untranslated region (3’UTR) resulting from alternative polyadenylation (APA) is emerging as a pervasive mechanism for regulating mRNA diversity, stability and translation. 

Though RNA-seq provides the whole-transcriptome information and a lot of tools for analyzing gene/isoform expression are available, very few tool focus on the analysis of 3'UTR from standard RNA-seq. DaPars is the first de novo tool that directly infers the dynamic alternative polyadenylation (APA) usage by comparing standard RNA-seq. Given the annotated gene model, DaPars can infer the de novo proximal APA sites as well as the long and short 3'UTR expression levels. Finally, the dynamic APA usages between two conditions will be identified.



![Flowchart](http://farm6.staticflickr.com/5533/12003068763_87e68075f6.jpg)
![Cancer](http://farm8.staticflickr.com/7459/8858567224_4b0f0214cf.jpg)


**News**
-----
**Sep, 2022**: DaPars was updated to 1.0.0 with the following changes (courtesy: Yi Zhang):
   1. Updated to python3
   2. Removed rpy2 and use python for the statistical test
   3. Fixed some minor bugs.




Mailing list
-----------
If you have questions, requests, or bugs to report, please email the [DaPars mailing list](https://groups.google.com/forum/#!forum/DaPars)

