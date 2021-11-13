#!/bin/bash
set -euxo pipefail
system=$1
datadir=$2
rep=$3
install_dir=$4
processcount=$5
threads=$6
result_sam_dir=$7
i=$8
output_sam=$result_sam_dir/${system}.th_${threads}.rep_${rep}.proc_${processcount}.${i}.sam

numactl --interleave=all -- ${install_dir}bwa mem -t ${threads} -K 100000000 ${datadir}/GCA_000001405.15_GRCh38_full_plus_hs38d1_analysis_set.fna ${datadir}/truncated.fq > ${output_sam}

