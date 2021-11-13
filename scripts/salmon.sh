#!/bin/bash
set -euxo pipefail
system=$1
datadir=$2
rep=$3
install_path=$4
result_sam_dir=$5
result_time_dir=$6

output_quant=${result_sam_dir}${system}.${rep}.quant.sf
salmon_timed_output=${result_time_dir}time_sys_${system}.rep_${rep}.time

/usr/bin/time -f "%U %S %e" -o ${salmon_timed_output} ${install_path}salmon quant -i ${datadir}/referenceGenome_index4/ -l A -1 ${datadir}/SRR10103759/C1_1.fq.gz -2 ${datadir}/SRR10103759/C1_2.fq.gz -o ${output_quant}

echo "$(<${salmon_timed_output})"
