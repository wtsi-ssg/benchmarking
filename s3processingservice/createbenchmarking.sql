CREATE DATABASE benchmarking
    WITH 
    OWNER = benchmarking
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_GB.utf8'
    LC_CTYPE = 'en_GB.utf8'
    CONNECTION LIMIT = -1;

CREATE TABLE public.returned_results
(
    id bigserial NOT NULL,
    jsondata jsonb NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE IF EXISTS public.returned_results
    OWNER to benchmarking;

CREATE MATERIALIZED VIEW IF NOT EXISTS public.cpu_results
TABLESPACE pg_default
AS
 SELECT benchmark_data.nickname,
    benchmark_data.benchmark_type,
    benchmark_data.processes,
    benchmark_data.threads,
    benchmark_data.usercpu,
    benchmark_data.elapsed,
    benchmark_data.maxrss,
    (benchmark_data.powerl -> 'cpu_energy'::text) -> 'value'::text AS cpu_energy,
    (benchmark_data.powerl -> 'ram_energy'::text) -> 'value'::text AS ram_energy
   FROM ( SELECT benchmark_runs.nickname,
            benchmark_runs.benchmark_type,
            benchmark_runs.processes,
            benchmark_runs.threads,
            benchmark_runs.runs -> 'user'::text AS usercpu,
            benchmark_runs.runs -> 'elapsed'::text AS elapsed,
            benchmark_runs.runs -> 'maxrss'::text AS maxrss,
            benchmark_runs.runs -> 'power'::text AS powerl
           FROM ( SELECT benchmarks.nickname,
                    benchmarks.benchmark_type,
                    benchmarks.benchmark_types -> 'processes'::text AS processes,
                    benchmarks.benchmark_types -> 'threads'::text AS threads,
                    jsonb_array_elements(benchmarks.benchmark_types -> 'runs'::text) AS runs
                   FROM ( SELECT hosts.nickname,
                            hosts.benchmark_type,
                            jsonb_array_elements((jsonb_array_elements(hosts.benchmark_types -> hosts.benchmark_type) -> 'results'::text) -> 'configurations'::text) AS benchmark_types
                           FROM ( SELECT maindata.jsondata -> 'nickname'::text AS nickname,
                                    jsonb_object_keys(((maindata.jsondata -> 'results'::text) -> 'CPU'::text) -> 'benchmarks'::text) AS benchmark_type,
                                    ((maindata.jsondata -> 'results'::text) -> 'CPU'::text) -> 'benchmarks'::text AS benchmark_types
                                   FROM ( SELECT returned_results.jsondata
   FROM returned_results) maindata) hosts
                          WHERE hosts.benchmark_type ~~ 'multithreaded_%'::text) benchmarks) benchmark_runs) benchmark_data
WITH DATA;

ALTER TABLE IF EXISTS public.cpu_results
    OWNER TO benchmarking;