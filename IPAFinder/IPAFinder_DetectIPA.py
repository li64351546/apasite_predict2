import itertools, collections, os, warnings
import numpy as np
from multiprocessing import Pool
import scipy as sp
import scipy.stats
from argparse import ArgumentParser,ArgumentTypeError
import HTSeq
parser = ArgumentParser(description="De novo analysis of Intronic Polyadenylation from standard RNA-seq (IpA analysis of replicated samples between two conditions)")
parser.add_argument("-b",dest='bamfiles',action="store",type=str,help="Input file with all bamfiles between two conditions")
parser.add_argument('-anno',dest='anno_txt',action="store",type=str,help="Input annotation file contains intron and flanking exons information")
parser.add_argument("-p",dest="processors",action="store",default=10,type=int,help="<INT> Number of processors used [default: 10]")
parser.add_argument("-o",dest="outfile",action="store",type=str,help="Output all inferred intronic poly(A) sites and their IPUI values")
args = parser.parse_args()
annot = collections.OrderedDict()
for line in open(args.anno_txt,"r"):
    gene_label,feature,rank,position,length,exon_rank_left,exon_rank_right = line.strip().split('\t')
    chrom,iv_str,strand = position.strip().split(':')
    start,end = map(int,iv_str.strip().split('-'))
    annot.setdefault(gene_label,[]).append((feature,int(rank),chrom,start,end,strand,int(length),exon_rank_left,exon_rank_right))


def parse_cfgfile(cfg_file):
    for line in open(cfg_file,"r"):
        lines = line.strip().split("=")
        if lines[0] == "condition1":
            bamfiles_condition1 = lines[1].split(",")
        if lines[0] == "condition2":
            bamfiles_condition2 = lines[1].split(",")
    return bamfiles_condition1,bamfiles_condition2

cigar_char = ('M', '=', 'X')
minaqual = 10
def invert_strand(iv):
    iv2 = iv.copy()
    if iv2.strand == "+":
        iv2.strand = "-"
    elif iv2.strand == "-":
        iv2.strand = "+"
    else:
        raise ValueError("Illegal strand")
    return iv2


def Get_label_information(label,annot,bam_reader):
    warnings.simplefilter("ignore")
    gas = HTSeq.GenomicArrayOfSets("auto", stranded=False)
    ga = HTSeq.GenomicArray("auto", stranded=False, typecode="i")
    gene_count = {}
    for feature,rank,chrom,start,end,strand,length,exon_rank_left,exon_rank_right in annot[label]:
        iv = HTSeq.GenomicInterval(chrom,start,end,strand)
        gas[iv] += (feature,rank)
        gene_count[(feature,rank)] = 0
    boundary_left,boundary_right = min([i[3] for i in annot[label]]),max([i[4] for i in annot[label]])
    region_fetch = annot[label][0][2]+":"+str(int(boundary_left)-500)+"-"+str(int(boundary_right)+500)
    read_seq = bam_reader.fetch(region=region_fetch)
    read_seq_iter = iter(bam_reader.fetch())
    one_read = next(read_seq_iter)
    pe_mode = one_read.paired_end
    if pe_mode:
        read_seq = HTSeq.pair_SAM_alignments_with_buffer(read_seq)
    for a in read_seq:
        if not pe_mode:
            if not a.aligned:
                continue
            if a.optional_field('NH') > 1:
                continue
            iv_seq = (cigop.ref_iv for cigop in a.cigar if cigop.type == "M" and cigop.size >0)
        else:
            if ((a[0] and a[0].aQual<minaqual) or (a[1] and a[1].aQual<minaqual)):
                continue
            if ((a[0] and a[0].optional_field('NH') > 1) or (a[1] and a[1].optional_field('NH')>1)):
                continue
            if a[0] is not None and a[0].aligned:
                iv_seq = (cigop.ref_iv for cigop in a[0].cigar if cigop.type in cigar_char and cigop.size > 0)
            else:
                iv_seq = tuple()
            if a[1] is not None and a[1].aligned:
                iv_seq = itertools.chain(iv_seq,(invert_strand(cigop.ref_iv) for cigop in a[1].cigar if cigop.type in cigar_char and cigop.size > 0))
        feature_aligned = set()
        for iv in iv_seq:
            for iv2, val2 in gas[iv].steps():
                feature_aligned |= val2
                ga[iv] += 1
        if len(feature_aligned) ==0:
            continue
        for f in [item for item in feature_aligned if item[0] == 'intron']:
            gene_count[f] +=1
        if 'intron' not in [x for x,y in feature_aligned]:
            for f in feature_aligned:
                gene_count[f] +=1
    return gas,ga,gene_count

def Get_Skipend_dict(region_fetch,bamfile,strand):
    bam_reader = HTSeq.BAM_Reader(bamfile)
    read_seq = bam_reader.fetch(region=region_fetch)
    read_seq_iter = iter(bam_reader.fetch())
    one_read = next(read_seq_iter)
    skip_list = []
    pe_mode = one_read.paired_end
    if pe_mode:
        read_seq = HTSeq.pair_SAM_alignments_with_buffer(read_seq)
    for a in read_seq:
        if not pe_mode:
            if not a.aligned:
                continue
            if a.optional_field('NH') > 1:
                continue
            if strand == "+":
                skip_list.extend([int(cigop.ref_iv.end) for cigop in a.cigar if cigop.type == "N" and cigop.size >0])
            else:
                skip_list.extend([int(cigop.ref_iv.start) for cigop in a.cigar if cigop.type == "N" and cigop.size >0])
        else:
            if ((a[0] and a[0].aQual<minaqual) or (a[1] and a[1].aQual<minaqual)):
                continue
            if ((a[0] and a[0].optional_field('NH') > 1) or (a[1] and a[1].optional_field('NH')>1)):
                continue
            if a[0] is not None and a[0].aligned:
                if strand == "+":
                    skip_list.extend([int(cigop.ref_iv.end) for cigop in a[0].cigar if cigop.type =="N" and cigop.size > 0])
                else:
                    skip_list.extend([int(cigop.ref_iv.start) for cigop in a[0].cigar if cigop.type =="N" and cigop.size > 0])
            if a[1] is not None and a[1].aligned:
                if strand == "+":
                    skip_list.extend([int(cigop.ref_iv.end) for cigop in a[1].cigar if cigop.type =="N" and cigop.size > 0])
                else:
                    skip_list.extend([int(cigop.ref_iv.start) for cigop in a[1].cigar if cigop.type =="N" and cigop.size > 0])
    skip_dict = dict(collections.Counter(skip_list))
    return skip_dict


def Get_Skipstart_dict(region_fetch,all_bamfiles,strand):
    skip_list = []
    for bamfile in all_bamfiles:
        bam_reader = HTSeq.BAM_Reader(bamfile)
        read_seq = bam_reader.fetch(region=region_fetch)
        read_seq_iter = iter(bam_reader.fetch())
        one_read = next(read_seq_iter)
        pe_mode = one_read.paired_end
        if pe_mode:
            read_seq = HTSeq.pair_SAM_alignments_with_buffer(read_seq)
        for a in read_seq:
            if not pe_mode:
                if not a.aligned:
                    continue
                if a.optional_field('NH') > 1:
                    continue
                if strand == "+":
                    skip_list.extend([int(cigop.ref_iv.start) for cigop in a.cigar if cigop.type == "N" and cigop.size >0])
                else:
                    skip_list.extend([int(cigop.ref_iv.end) for cigop in a.cigar if cigop.type == "N" and cigop.size >0])
            else:
                if ((a[0] and a[0].aQual<minaqual) or (a[1] and a[1].aQual<minaqual)):
                    continue
                if ((a[0] and a[0].optional_field('NH') > 1) or (a[1] and a[1].optional_field('NH')>1)):
                    continue
                if a[0] is not None and a[0].aligned:
                    if strand == "+":
                        skip_list.extend([int(cigop.ref_iv.start) for cigop in a[0].cigar if cigop.type =="N" and cigop.size > 0])
                    else:
                        skip_list.extend([int(cigop.ref_iv.end) for cigop in a[0].cigar if cigop.type =="N" and cigop.size > 0])
                if a[1] is not None and a[1].aligned:
                    if strand == "+":
                        skip_list.extend([int(cigop.ref_iv.start) for cigop in a[1].cigar if cigop.type =="N" and cigop.size > 0])
                    else:
                        skip_list.extend([int(cigop.ref_iv.end) for cigop in a[1].cigar if cigop.type =="N" and cigop.size > 0])
    skip_dict = dict(collections.Counter(skip_list))
    return skip_dict

def Estimation_abundance(Region_Coverage,break_point):
    downstream_cov_mean = np.mean(Region_Coverage[break_point:])
    upstream_cov_mean = np.mean(Region_Coverage[:break_point])
    Coverage_diff = Region_Coverage[0:break_point]-upstream_cov_mean
    Coverage_diff = np.append(Coverage_diff,Region_Coverage[break_point:]-downstream_cov_mean)
    Mean_Squared_error = np.mean(Coverage_diff**2)
    return Mean_Squared_error


def Get_min_mseratio_list(cvg_region_list):
    search_result = [[],[]]
    global_mse_list = [np.mean((cvg_region-np.mean(cvg_region))**2) for cvg_region in cvg_region_list]
    for curr_num in range(len(cvg_region_list)):
        curr_cvg_result = [[],[]]
        for curr_search_point in range(50,len(cvg_region_list[curr_num]),int(len(cvg_region_list[curr_num])/30)):
            Mean_Squared_error = Estimation_abundance(cvg_region_list[curr_num], curr_search_point)
            mse_ratio = Mean_Squared_error/global_mse_list[curr_num]
            curr_cvg_result[0].append(mse_ratio)
            curr_cvg_result[1].append(curr_search_point)
        curr_cvg_min_mse = min(curr_cvg_result[0])
        curr_cvg_min_mse_index = curr_cvg_result[0].index(curr_cvg_min_mse)
        curr_cvg_min_mse_point = curr_cvg_result[1][curr_cvg_min_mse_index]
        search_result[0].append(curr_cvg_min_mse)
        search_result[1].append(curr_cvg_min_mse_point)
    return search_result


def Get_min_mseratio_list_refine(cvg_region_list,min_mse_point):
    research_result = [[],[]]
    global_mse_list = [np.mean((cvg_region-np.mean(cvg_region))**2) for cvg_region in cvg_region_list]
    for curr_num in range(len(cvg_region_list)):
        curr_cvg_result = [[],[]]
        for curr_search_point in range(min_mse_point-int(len(cvg_region_list[curr_num])/30),min_mse_point+int(len(cvg_region_list[curr_num])/30),30):
            Mean_Squared_error = Estimation_abundance(cvg_region_list[curr_num], curr_search_point)
            mse_ratio = Mean_Squared_error/global_mse_list[curr_num]
            curr_cvg_result[0].append(mse_ratio)
            curr_cvg_result[1].append(curr_search_point)
        curr_cvg_min_mse = min(curr_cvg_result[0])
        curr_cvg_min_mse_index = curr_cvg_result[0].index(curr_cvg_min_mse)
        curr_cvg_min_mse_point = curr_cvg_result[1][curr_cvg_min_mse_index]
        research_result[0].append(curr_cvg_min_mse)
        research_result[1].append(curr_cvg_min_mse_point)
    return research_result


def get_exon_count(curr_label_all_gene_count,label):
    rank_list = [feature[1] for feature in annot[label] if feature[0]=='exon']
    SYMBOL = label.split(":")[1].split("|")[0]
    result = []
    for rank in rank_list:
        a = [SYMBOL+":"+"exon_"+str(rank)] + [curr_label_all_gene_count[i][('exon',rank)] for i in range(len(curr_label_all_gene_count))]
        result.append(a)
    return result


def Get_IPAsite_IPUI(input_tuple):
    IPAevent,curr_label_all_ga,gas = input_tuple
    label,intron_rank,IPA_inf,IPAtype = IPAevent.split(";")
    intronrank = int(intron_rank.split("_")[1])
    position_list = list(map(int,IPA_inf.split(":")[1].split('-')))
    SYMBOL = label.split(":")[1].split("|")[0]
    result = []
    for feature,rank,chrom,start,end,strand,length,exon_rank_left,exon_rank_right in annot[label]:
        if feature == "intron" and int(rank) == intronrank:
            iv = HTSeq.GenomicInterval(chrom,start,end,strand)
            IPAstart = position_list[0]-int(start)
            IPA_location = position_list[1]-int(start)
            curr_label_all_cov = []
            for ga in curr_label_all_ga:
                if strand == "-":
                    curr_label_all_cov.append(list(ga[iv])[::-1])
                    IPAstart = int(end)-position_list[1]
                    IPA_location = int(end)-position_list[0]
                else:
                    curr_label_all_cov.append(list(ga[iv]))
            IPA_isoform_abundance = [np.mean(cvg_region[IPAstart:(IPAstart+int(int((IPA_location-IPAstart)/1.5)))]) for cvg_region in curr_label_all_cov]
            if strand == "+":
                exon_iv = tuple(i[0] for i in gas.steps() if i[1] == {('exon',int(exon_rank_left))})
            else:
                exon_iv = tuple(i[0] for i in gas.steps() if i[1] == {('exon',int(exon_rank_right))})
            if len(exon_iv) == 1:
                exon_abundance = [np.mean(sorted(list(ga[exon_iv[0]]),reverse=True)[:30]) for ga in curr_label_all_ga]
                if sum(np.array(exon_abundance)>10) == len(all_bamfiles) and sum(np.array([x-y for x,y in zip(exon_abundance,IPA_isoform_abundance)])>0)>len(all_bamfiles)*0.5:
                    IPARatio_list = [round(x/y,3) for x,y in zip(IPA_isoform_abundance,exon_abundance)]
                    IPUI_condition_diff = np.mean(np.array(IPARatio_list[num_condition1:])) - np.mean(np.array(IPARatio_list[:num_condition1]))
                    result = [SYMBOL,intron_rank,IPA_inf,IPAtype]+IPARatio_list+[IPUI_condition_diff]
    return result



def Get_IPAevent(input_tuple):
    label,all_bamfiles = input_tuple
    SYMBOL = label.split(":")[1].split("|")[0]
    curr_label_all_gas = []
    curr_label_all_ga = []
    curr_label_all_gene_count = []
    IPA_result = []
    for bamfile in all_bamfiles:
        bam_reader = HTSeq.BAM_Reader(bamfile)
        gas,ga,gene_count = Get_label_information(label,annot,bam_reader)
        curr_label_all_gas.append(gas)
        curr_label_all_ga.append(ga)
        curr_label_all_gene_count.append(gene_count)
    exon_count_list = get_exon_count(curr_label_all_gene_count,label)
    for feature,rank,chrom,start,end,strand,length,exon_rank_left,exon_rank_right in annot[label]:
        if feature == "intron" and int(length)>250:
            intron_start = start
            intron_end = end
            end_value = 15
            index_list = [index for index,gene_count in enumerate(curr_label_all_gene_count) if gene_count[('intron',rank)]>50]
            if index_list != []:
                iv = HTSeq.GenomicInterval(chrom,intron_start,intron_end,strand)
                IPAtype = "Composite"
                curr_label_all_cov = []
                for index in index_list:
                    if strand == "-":
                        curr_label_all_cov.append(list(curr_label_all_ga[index][iv])[::-1])
                    else:
                        curr_label_all_cov.append(list(curr_label_all_ga[index][iv]))
                intron_region = chrom+":"+str(intron_start)+"-"+str(intron_end)
                skipend_dict_list = [Get_Skipend_dict(intron_region,bamfile,strand) for bamfile in all_bamfiles]
                for index,skipend_dict in enumerate(skipend_dict_list):
                    for key,value in skipend_dict.items():
                        if int(start)+50 < int(key) < int(end)-50 and int(value)>10:
                            if strand == "+":
                                skip_position = int(key)-int(start)
                            else:
                                skip_position = int(end)-int(key)
                            curr_label_all_cov = [cvg_region[skip_position:] for cvg_region in curr_label_all_cov]
                            IPAtype = "Skipped"
                            start = int(key)
                            end = int(key)
                            end_value = int(value)
                            break
                    else:
                        continue
                    break
                min_mseratio_list,min_mse_point_list = Get_min_mseratio_list(curr_label_all_cov)
                min_mseratio = min(min_mseratio_list)
                min_mseratio_index = min_mseratio_list.index(min_mseratio)
                if min_mseratio < 0.5:
                    min_mseratio_list_refine,min_mse_point_list_refine = Get_min_mseratio_list_refine(curr_label_all_cov,min_mse_point_list[min_mseratio_index])
                    min_mseratio_refine = min(min_mseratio_list_refine)
                    min_mseratio_index_refine = min_mseratio_list_refine.index(min_mseratio_refine)
                    IPA_point = int(min_mse_point_list_refine[min_mseratio_index_refine])
                    up_down_diff = max([np.mean(coverage[:IPA_point])-np.mean(coverage[IPA_point:]) for coverage in curr_label_all_cov])
                    upstream_cov = max([len(list(filter(lambda x:x>5,coverage[:IPA_point])))/IPA_point for coverage in curr_label_all_cov])
                    downstream_cov = min([len(list(filter(lambda x:x>5,coverage[IPA_point:])))/(len(coverage)-IPA_point) for coverage in curr_label_all_cov])
                    if min_mseratio_refine < 0.5 and up_down_diff > 1 and upstream_cov > 0.8 and downstream_cov < 0.5:
                        if strand == "+":
                            IPA_location = int(start) + IPA_point
                            IPA_inf = chrom + ":" + str(start) + "-" + str(IPA_location)
                        else:
                            IPA_location = int(end) - IPA_point
                            IPA_inf = chrom+":" + str(IPA_location) + "-" + str(end)
                        skipstart_dict = Get_Skipstart_dict(intron_region,all_bamfiles,strand)
                        for key,value in skipstart_dict.items():
                            if IPA_location-20 < int(key) < IPA_location+20 and int(value) > end_value*0.8:
                                break
                        else:
                            intronPA_inf = label + ";"+feature + "_" + str(rank) + ";" + IPA_inf + ";" +  IPAtype
                            IPA_information = Get_IPAsite_IPUI((intronPA_inf,curr_label_all_ga,gas))
                            IPA_result.append(IPA_information)
                            exon_count_list.append([SYMBOL + ":"+feature + "_" + str(rank)] + [curr_label_all_gene_count[i][('intron',rank)] for i in range(len(curr_label_all_gene_count))])
    return IPA_result,exon_count_list


def output_IPUI(outfile,all_bamfiles,result_list):
    out_IPUI = open(outfile,"w")
    first_line = ["SYMBOL","intron_rank","Terminal_exon","IPAtype"]
    filenames = [bamfile.split("/")[-1].split(".")[0] for bamfile in all_bamfiles]
    first_line = first_line + filenames + ["IPUI_diff"]
    out_IPUI.writelines("\t".join(first_line)+"\n")
    for gene_list in result_list:
        if gene_list[0] != []:
            for IPA_lst in gene_list[0]:
                if IPA_lst != []:
                    out_IPUI.writelines('\t'.join(list(map(str,IPA_lst)))+'\n')
    out_IPUI.close()


def output_exoncount(all_bamfiles,result_list):
    if os.path.exists("project/") == False:
        os.makedirs("project/")
    for i in range(len(all_bamfiles)):
        bamfile_name = all_bamfiles[i]
        out = open("project/" + bamfile_name.split("/")[-1].split(".")[0] + "_exoncount.txt","w")
        for gene_list in result_list:
            for exon_lst in gene_list[1]:
                out.write("{}\t{}\n".format(exon_lst[0],exon_lst[i+1]))
        out.close()


bamfiles_condition1,bamfiles_condition2 = parse_cfgfile(args.bamfiles)

all_bamfiles = bamfiles_condition1 + bamfiles_condition2
num_condition1 = len(bamfiles_condition1)
pool = Pool(args.processors)
input_tuple = list(zip(annot.keys(),[all_bamfiles]*len(annot)))
result_list = pool.map(Get_IPAevent,input_tuple)
output_IPUI(args.outfile,all_bamfiles,result_list)
output_exoncount(all_bamfiles,result_list)
