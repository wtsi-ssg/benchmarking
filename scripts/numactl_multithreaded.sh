#!/bin/bash
set -euxo pipefail
system=$1
datadir=$2
rep=$3
install_dir=$4
processcount=$5
threads=$6
result_sam_dir=$7
result_time_dir=$8
scriptdir=`dirname "$0"`

numa_timed_output=${result_time_dir}/time_sys_${system}.th_${threads}.rep_${rep}.proc_${processcount}.time

/usr/bin/time -f "%U %S %e" -o ${numa_timed_output} bash -c \
	"(for i in $(bash -c "echo {1..$processcount}"); do echo \$i; done)| parallel --verbose -j 0 -P +$processcount -- ${scriptdir}/numactl_multithreaded_inner.sh $system $datadir $rep $install_dir $processcount $threads $result_sam_dir {}"

echo "$(<${numa_timed_output})"
