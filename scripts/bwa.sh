#!/bin/bash
set -euxo pipefail
system=$1
datadir=$2
rep=$3
install_path=$4
result_sam_dir=$5
result_time_dir=$6

output_sam=${result_sam_dir}${system}.${rep}.sam
bwa_timed_output=${result_time_dir}time_sys_${system}.rep_${rep}.time

/usr/bin/time -f "%U %S %e" -o ${bwa_timed_output} ${install_path}bwa mem -K 100000000 ${datadir}/GCA_000001405.15_GRCh38_full_plus_hs38d1_analysis_set.fna ${datadir}/truncated.fq > ${output_sam}

echo "$(<${bwa_timed_output})"
