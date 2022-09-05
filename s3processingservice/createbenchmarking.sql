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

-- View: public.cpu_results

CREATE MATERIALIZED VIEW IF NOT EXISTS public.cpu_results
TABLESPACE pg_default
AS
 SELECT benchmark_data.nickname,
    benchmark_data.benchmark_type,
    benchmark_data.processes::integer AS processes,
    benchmark_data.threads::integer AS threads,
    benchmark_data.usercpu::numeric AS usercpu,
    benchmark_data.syscpu::numeric AS syscpu,
    benchmark_data.elapsed::numeric AS elapsed,
    benchmark_data.maxrss::integer AS maxrss,
    ((benchmark_data.powerl -> 'cpu_energy'::text) ->> 'value'::text)::numeric AS cpu_energy,
    ((benchmark_data.powerl -> 'ram_energy'::text) ->> 'value'::text)::numeric AS ram_energy
   FROM ( SELECT benchmark_runs.nickname,
            benchmark_runs.benchmark_type,
            benchmark_runs.processes,
            benchmark_runs.threads,
            benchmark_runs.runs ->> 'user'::text AS usercpu,
            benchmark_runs.runs ->> 'system'::text AS syscpu,
            benchmark_runs.runs ->> 'elapsed'::text AS elapsed,
            benchmark_runs.runs ->> 'maxrss'::text AS maxrss,
            benchmark_runs.runs -> 'power'::text AS powerl
           FROM ( SELECT benchmarks.nickname,
                    benchmarks.benchmark_type,
                    benchmarks.benchmark_types ->> 'processes'::text AS processes,
                    benchmarks.benchmark_types ->> 'threads'::text AS threads,
                    jsonb_array_elements(benchmarks.benchmark_types -> 'runs'::text) AS runs
                   FROM ( SELECT hosts.nickname,
                            hosts.benchmark_type,
                            jsonb_array_elements((jsonb_array_elements(hosts.benchmark_types -> hosts.benchmark_type) -> 'results'::text) -> 'configurations'::text) AS benchmark_types
                           FROM ( SELECT returned_results.jsondata ->> 'nickname'::text AS nickname,
                                    jsonb_object_keys(((returned_results.jsondata -> 'results'::text) -> 'CPU'::text) -> 'benchmarks'::text) AS benchmark_type,
                                    ((returned_results.jsondata -> 'results'::text) -> 'CPU'::text) -> 'benchmarks'::text AS benchmark_types
                                   FROM returned_results) hosts
                          WHERE hosts.benchmark_type ~~ 'multithreaded_%'::text) benchmarks) benchmark_runs) benchmark_data
WITH DATA;

ALTER TABLE IF EXISTS public.cpu_results
    OWNER TO benchmarking;
-- View: public.mbw_results

-- DROP MATERIALIZED VIEW IF EXISTS public.mbw_results;

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mbw_results
TABLESPACE pg_default
AS
 SELECT benchmarks.nickname,
    (benchmarks.mbw_results ->> 'MiB'::text)::numeric AS mib,
    split_part(benchmarks.mbw_results ->> 'copy'::text, ' ', 1)::numeric AS copyrate,
    split_part(benchmarks.mbw_results ->> 'copy'::text, ' ', 2) AS copyrateunits,
    (benchmarks.mbw_results ->> 'elapsed'::text)::numeric AS elapsed,
    (benchmarks.mbw_results ->> 'iteration'::text)::integer AS iteration,
    benchmarks.mbw_results ->> 'method'::text AS method
   FROM ( SELECT hosts.nickname,
            jsonb_array_elements(jsonb_array_elements(hosts.benchmark_types -> 'mbw'::text) -> 'results'::text) AS mbw_results
           FROM ( SELECT returned_results.jsondata ->> 'nickname'::text AS nickname,
                    ((returned_results.jsondata -> 'results'::text) -> 'CPU'::text) -> 'benchmarks'::text AS benchmark_types
                   FROM returned_results) hosts) benchmarks
WITH DATA;

ALTER TABLE IF EXISTS public.mbw_results
    OWNER TO benchmarking;

CREATE MATERIALIZED VIEW public.iozone_results
AS
SELECT 
nickname,
iz_report_types,
x,
y::integer,
(y_data ->> y)::integer z
FROM (
SELECT
nickname,
iz_report_types,
x::integer,
jsonb_object_keys(x_data -> x) y,
x_data -> x as y_data
FROM(
	SELECT nickname,
iz_report_types,
jsonb_object_keys(iz_report_type -> iz_report_types) x,
iz_report_type -> iz_report_types AS x_data
FROM
(SELECT nickname,
jsonb_object_keys(iozone_benchmarks -> 'results') as iz_report_types,
iozone_benchmarks -> 'results' AS iz_report_type
FROM
(SELECT returned_results.jsondata ->> 'nickname'::text AS nickname,
                                    jsonb_array_elements(returned_results.jsondata -> 'results'::text -> 'Disk'::text  -> 'benchmarks' -> 'IOZone'::text) AS iozone_benchmarks
                                   FROM returned_results) as izb) as isbr) isbr_x ) isbr_xy
WITH DATA;

ALTER TABLE IF EXISTS public.iozone_results
    OWNER TO benchmarking;
