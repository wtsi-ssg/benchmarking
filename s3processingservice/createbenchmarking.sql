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
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.returned_results
    OWNER to benchmarking;

-- Table: public.ci_returned_results

-- DROP TABLE IF EXISTS public.ci_returned_results;

CREATE TABLE IF NOT EXISTS public.ci_returned_results
(
    id bigserial NOT NULL,
    jsondata jsonb NOT NULL,
    CONSTRAINT ci_returned_results_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.returned_results
    OWNER to benchmarking;
    
-- Table: public.nickname_year

-- DROP TABLE IF EXISTS public.nickname_year;

CREATE TABLE IF NOT EXISTS public.nickname_year
(
    id bigserial NOT NULL,
    nickname character varying COLLATE pg_catalog."default" NOT NULL,
    year integer NOT NULL,
    CONSTRAINT nickname_year_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.nickname_year
    OWNER to benchmarking;

-- View: public.cpu_results

-- DROP MATERIALIZED VIEW IF EXISTS public.cpu_results;

CREATE MATERIALIZED VIEW IF NOT EXISTS public.cpu_results
TABLESPACE pg_default
AS
 SELECT benchmark_data.nickname,
    benchmark_data.cpu_model,
    benchmark_data.run_date,
    benchmark_data.benchmark_type,
    benchmark_data.program_name,
    benchmark_data.program_version,
    benchmark_data.units,
    benchmark_data.cpu_affinity,
    benchmark_data.processes::integer AS processes,
    benchmark_data.threads::integer AS threads,
    benchmark_data.usercpu::numeric AS usercpu,
    benchmark_data.syscpu::numeric AS syscpu,
    benchmark_data.elapsed::numeric AS elapsed,
    benchmark_data.maxrss::integer AS maxrss,
    ((benchmark_data.powerl -> 'cpu_energy'::text) ->> 'value'::text)::numeric AS cpu_energy,
    ((benchmark_data.powerl -> 'ram_energy'::text) ->> 'value'::text)::numeric AS ram_energy,
    benchmark_data.repeatnum
   FROM ( SELECT benchmark_runs.nickname,
		    benchmark_runs.cpu_model,
            benchmark_runs.run_date,
            benchmark_runs.benchmark_type,
            benchmark_runs.program_name,
            benchmark_runs.program_version,
            benchmark_runs.units,
            benchmark_runs.cpu_affinity,
            benchmark_runs.processes,
            benchmark_runs.threads,
            benchmark_runs.runs ->> 'user'::text AS usercpu,
            benchmark_runs.runs ->> 'system'::text AS syscpu,
            benchmark_runs.runs ->> 'elapsed'::text AS elapsed,
            benchmark_runs.runs ->> 'maxrss'::text AS maxrss,
            benchmark_runs.runs -> 'power'::text AS powerl,
            row_number() OVER (PARTITION BY benchmark_runs.nickname, benchmark_runs.benchmark_type, benchmark_runs.cpu_affinity, benchmark_runs.processes, benchmark_runs.threads) AS repeatnum
           FROM ( SELECT benchmarks.nickname,
				    benchmarks.cpu_model,
                    benchmarks.run_date,
                    benchmarks.benchmark_type,
                    benchmarks.program_name,
                    benchmarks.program_version,
                    benchmarks.units,
                    benchmarks.cpu_affinity,
                    benchmarks.benchmark_types ->> 'processes'::text AS processes,
                    benchmarks.benchmark_types ->> 'threads'::text AS threads,
                    jsonb_array_elements(benchmarks.benchmark_types -> 'runs'::text) AS runs
                   FROM ( SELECT hosts.nickname,
						    hosts.cpu_model,
                            hosts.run_date,
                            hosts.benchmark_type,
                            (jsonb_array_elements(hosts.benchmark_types -> hosts.benchmark_type) -> 'settings'::text) ->> 'program'::text AS program_name,
                            (jsonb_array_elements(hosts.benchmark_types -> hosts.benchmark_type) -> 'settings'::text) ->> 'programversion'::text AS program_version,
                            (jsonb_array_elements(hosts.benchmark_types -> hosts.benchmark_type) -> 'settings'::text) ->> 'units'::text AS units,
                            (jsonb_array_elements(hosts.benchmark_types -> hosts.benchmark_type) -> 'settings'::text) ->> 'cpu_affinity'::text AS cpu_affinity,
                            jsonb_array_elements((jsonb_array_elements(hosts.benchmark_types -> hosts.benchmark_type) -> 'results'::text) -> 'configurations'::text) AS benchmark_types
                           FROM ( SELECT returned_results.jsondata ->> 'nickname'::text AS nickname,
								    returned_results.jsondata -> 'system-info'->> 'model'::text AS cpu_model,
                                    returned_results.jsondata ->> 'date'::text AS run_date,
                                    jsonb_object_keys(((returned_results.jsondata -> 'results'::text) -> 'CPU'::text) -> 'benchmarks'::text) AS benchmark_type,
                                    ((returned_results.jsondata -> 'results'::text) -> 'CPU'::text) -> 'benchmarks'::text AS benchmark_types
                                   FROM returned_results) hosts
                          WHERE hosts.benchmark_type ~~ 'multithreaded_%'::text) benchmarks) benchmark_runs) benchmark_data
WITH DATA;

ALTER TABLE IF EXISTS public.cpu_results
    OWNER TO benchmarking;

-- View: public.ci_cpu_results

-- DROP MATERIALIZED VIEW IF EXISTS public.ci_cpu_results;

CREATE MATERIALIZED VIEW IF NOT EXISTS public.ci_cpu_results
TABLESPACE pg_default
AS
 SELECT benchmark_data.testname,
    benchmark_data.tag,
	benchmark_data.revision,
	benchmark_data.commit_datetime,
    benchmark_data.benchmark_type,
    benchmark_data.program_name,
    benchmark_data.program_version,
    benchmark_data.units,
    benchmark_data.processes::integer AS processes,
    benchmark_data.threads::integer AS threads,
    benchmark_data.usercpu::numeric AS usercpu,
    benchmark_data.syscpu::numeric AS syscpu,
    benchmark_data.elapsed::numeric AS elapsed,
    benchmark_data.maxrss::integer AS maxrss,
    ((benchmark_data.powerl -> 'cpu_energy'::text) ->> 'value'::text)::numeric AS cpu_energy,
    ((benchmark_data.powerl -> 'ram_energy'::text) ->> 'value'::text)::numeric AS ram_energy
   FROM ( SELECT benchmark_runs.testname,
            benchmark_runs.tag,
			benchmark_runs.revision,
			benchmark_runs.commit_datetime,
            benchmark_runs.benchmark_type,
            benchmark_runs.program_name,
            benchmark_runs.program_version,
            benchmark_runs.units,
            benchmark_runs.processes,
            benchmark_runs.threads,
            benchmark_runs.runs ->> 'user'::text AS usercpu,
            benchmark_runs.runs ->> 'system'::text AS syscpu,
            benchmark_runs.runs ->> 'elapsed'::text AS elapsed,
            benchmark_runs.runs ->> 'maxrss'::text AS maxrss,
            benchmark_runs.runs -> 'power'::text AS powerl
           FROM ( SELECT benchmarks.testname,
                    benchmarks.tag,
					benchmarks.revision,
					benchmarks.commit_datetime,
                    benchmarks.benchmark_type,
                    benchmarks.program_name,
                    benchmarks.program_version,
                    benchmarks.units,
                    benchmarks.benchmark_types ->> 'processes'::text AS processes,
                    benchmarks.benchmark_types ->> 'threads'::text AS threads,
                    jsonb_array_elements(benchmarks.benchmark_types -> 'runs'::text) AS runs
                   FROM ( SELECT hosts.testname,
                            hosts.tag,
						    hosts.revision,
						    hosts.commit_datetime,
                            hosts.benchmark_type,
                            ((hosts.benchmark_types -> hosts.benchmark_type) -> 'settings'::text) ->> 'program'::text AS program_name,
                            ((hosts.benchmark_types -> hosts.benchmark_type) -> 'settings'::text) ->> 'programversion'::text AS program_version,
                            ((hosts.benchmark_types -> hosts.benchmark_type) -> 'settings'::text) ->> 'units'::text AS units,
                            jsonb_array_elements(((hosts.benchmark_types -> hosts.benchmark_type) -> 'results'::text) -> 'configurations'::text) AS benchmark_types
                           FROM ( SELECT ci_returned_results.jsondata ->> 'name'::text AS testname,
                                    ci_returned_results.jsondata ->> 'tag'::text AS tag,
								    ci_returned_results.jsondata ->> 'revision'::text AS revision,
								    ci_returned_results.jsondata ->> 'datetime'::text AS commit_datetime,
                                    jsonb_object_keys((ci_returned_results.jsondata -> 'results'::text) -> 'results'::text) AS benchmark_type,
                                    (ci_returned_results.jsondata -> 'results'::text) -> 'results'::text AS benchmark_types
                                   FROM ci_returned_results) hosts
                          WHERE hosts.benchmark_type ~~ 'multithreaded_%'::text) benchmarks) benchmark_runs) benchmark_data
WITH DATA;

ALTER TABLE IF EXISTS public.ci_cpu_results
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

-- View: public.cpu_corecount

-- DROP MATERIALIZED VIEW IF EXISTS public.cpu_corecount;

CREATE MATERIALIZED VIEW IF NOT EXISTS public.cpu_corecount
TABLESPACE pg_default
AS
 SELECT DISTINCT returned_results.jsondata ->> 'nickname'::text AS nickname,
    (((returned_results.jsondata -> 'system-info'::text) -> 'cpuinfo'::text) ->> 'count'::text)::integer AS corecount,
    nickname_year.year
   FROM returned_results
     LEFT JOIN nickname_year ON (returned_results.jsondata ->> 'nickname'::text) = nickname_year.nickname::text
WITH DATA;

ALTER TABLE IF EXISTS public.cpu_corecount
    OWNER TO benchmarking;

-- View: public.geekbench5_results

-- DROP MATERIALIZED VIEW IF EXISTS public.geekbench5_results;

CREATE MATERIALIZED VIEW IF NOT EXISTS public.geekbench5_results
TABLESPACE pg_default
AS
 SELECT benchmarks.nickname,
    (benchmarks.geekbench5_results ->> 'score'::text)::numeric AS ovarall_score,
    (benchmarks.geekbench5_results ->> 'runtime'::text)::numeric AS overall_runtime,
    (benchmarks.geekbench5_results ->> 'multicore_score'::text)::numeric AS multicore_score,
    nickname_year.year
   FROM ( SELECT hosts.nickname,
            (jsonb_array_elements(hosts.benchmark_types -> 'GeekBench5'::text) -> 'results'::text) -> 'result_summary'::text AS geekbench5_results
           FROM ( SELECT returned_results.jsondata ->> 'nickname'::text AS nickname,
                    ((returned_results.jsondata -> 'results'::text) -> 'CPU'::text) -> 'benchmarks'::text AS benchmark_types
                   FROM returned_results) hosts) benchmarks
     LEFT JOIN nickname_year ON benchmarks.nickname = nickname_year.nickname::text
WITH DATA;

ALTER TABLE IF EXISTS public.geekbench5_results
    OWNER TO benchmarking;

-- View: public.geekbench5_detailed_results

-- DROP MATERIALIZED VIEW IF EXISTS public.geekbench5_detailed_results;

CREATE MATERIALIZED VIEW IF NOT EXISTS public.geekbench5_detailed_results
TABLESPACE pg_default
AS
 SELECT benchmarks.nickname,
    benchmarks.section_name,
    benchmarks.geekbench5_results ->> 'name'::text AS detail_name,
    (benchmarks.geekbench5_results ->> 'score'::text)::numeric AS detail_score,
    nickname_year.year
   FROM ( SELECT benchmark_section.nickname,
            benchmark_section.geekbench5_results ->> 'name'::text AS section_name,
            jsonb_array_elements(benchmark_section.geekbench5_results -> 'workloads'::text) AS geekbench5_results
           FROM ( SELECT hosts.nickname,
                    jsonb_array_elements(((jsonb_array_elements(hosts.benchmark_types -> 'GeekBench5'::text) -> 'results'::text) -> 'result_summary'::text) -> 'sections'::text) AS geekbench5_results
                   FROM ( SELECT returned_results.jsondata ->> 'nickname'::text AS nickname,
                            ((returned_results.jsondata -> 'results'::text) -> 'CPU'::text) -> 'benchmarks'::text AS benchmark_types
                           FROM returned_results) hosts) benchmark_section) benchmarks
     LEFT JOIN nickname_year ON benchmarks.nickname = nickname_year.nickname::text
WITH DATA;

ALTER TABLE IF EXISTS public.geekbench5_detailed_results
    OWNER TO benchmarking;

-- View: public.cpu_results_best_avg_elapsed

-- DROP VIEW public.cpu_results_best_avg_elapsed;

CREATE OR REPLACE VIEW public.cpu_results_best_avg_elapsed
 AS
 WITH avg_elapsed_agg AS (
         SELECT cpu_results_1.nickname,
            cpu_results_1.benchmark_type,
            cpu_results_1.program_name,
            cpu_results_1.program_version,
            cpu_results_1.units,
            cpu_results_1.cpu_affinity,
            cpu_results_1.processes,
            cpu_results_1.threads,
            avg(cpu_results_1.elapsed) AS avg_elapsed
           FROM cpu_results cpu_results_1
          GROUP BY cpu_results_1.nickname, cpu_results_1.benchmark_type, cpu_results_1.program_name, cpu_results_1.program_version, cpu_results_1.units, cpu_results_1.cpu_affinity, cpu_results_1.processes, cpu_results_1.threads
        ), min_avg_elapsed_agg AS (
         SELECT avg_elapsed_agg.nickname,
            avg_elapsed_agg.benchmark_type,
            avg_elapsed_agg.program_name,
            avg_elapsed_agg.program_version,
            avg_elapsed_agg.units,
            avg_elapsed_agg.cpu_affinity,
            min(avg_elapsed_agg.avg_elapsed) AS min_avg_elapsed
           FROM avg_elapsed_agg
          GROUP BY avg_elapsed_agg.nickname, avg_elapsed_agg.benchmark_type, avg_elapsed_agg.program_name, avg_elapsed_agg.program_version, avg_elapsed_agg.units, avg_elapsed_agg.cpu_affinity
        ), avg_elapsed_agg_config AS (
         SELECT avg_elapsed_agg.nickname,
            avg_elapsed_agg.benchmark_type,
            avg_elapsed_agg.program_name,
            avg_elapsed_agg.program_version,
            avg_elapsed_agg.units,
            avg_elapsed_agg.cpu_affinity,
            avg_elapsed_agg.processes,
            avg_elapsed_agg.threads,
            avg_elapsed_agg.avg_elapsed
           FROM avg_elapsed_agg
             JOIN min_avg_elapsed_agg ON avg_elapsed_agg.avg_elapsed = min_avg_elapsed_agg.min_avg_elapsed AND avg_elapsed_agg.nickname = min_avg_elapsed_agg.nickname AND avg_elapsed_agg.benchmark_type = min_avg_elapsed_agg.benchmark_type AND avg_elapsed_agg.program_name = min_avg_elapsed_agg.program_name AND avg_elapsed_agg.program_version = min_avg_elapsed_agg.program_version AND avg_elapsed_agg.units = min_avg_elapsed_agg.units AND avg_elapsed_agg.cpu_affinity = min_avg_elapsed_agg.cpu_affinity
        )
 SELECT cpu_results.nickname,
	cpu_results.run_date,
	cpu_results.cpu_model,
    cpu_results.benchmark_type,
    cpu_results.program_name,
    cpu_results.program_version,
    cpu_results.units,
    cpu_results.cpu_affinity,
    cpu_results.processes,
    cpu_results.threads,
    cpu_results.usercpu,
    cpu_results.syscpu,
    cpu_results.elapsed,
    cpu_results.maxrss,
    cpu_results.cpu_energy,
    cpu_results.ram_energy,
    cpu_results.repeatnum
   FROM cpu_results
     JOIN avg_elapsed_agg_config ON cpu_results.nickname = avg_elapsed_agg_config.nickname AND cpu_results.benchmark_type = avg_elapsed_agg_config.benchmark_type AND cpu_results.program_name = avg_elapsed_agg_config.program_name AND cpu_results.program_version = avg_elapsed_agg_config.program_version AND cpu_results.units = avg_elapsed_agg_config.units AND cpu_results.cpu_affinity = avg_elapsed_agg_config.cpu_affinity AND cpu_results.processes = avg_elapsed_agg_config.processes AND cpu_results.threads = avg_elapsed_agg_config.threads;

ALTER TABLE public.cpu_results_best_avg_elapsed
    OWNER TO benchmarking;

-- View: public.cpu_results_best_avg_throughput

-- DROP VIEW public.cpu_results_best_avg_throughput;

CREATE OR REPLACE VIEW public.cpu_results_best_avg_throughput
 AS
 WITH avg_throughput_agg AS (
         SELECT cpu_results_1.nickname,
            cpu_results_1.benchmark_type,
            cpu_results_1.program_name,
            cpu_results_1.program_version,
            cpu_results_1.units,
            cpu_results_1.cpu_affinity,
            cpu_results_1.processes,
            cpu_results_1.threads,
            avg(cpu_results_1.processes/(cpu_results_1.elapsed/3600)) AS avg_throughput
           FROM cpu_results cpu_results_1
          GROUP BY cpu_results_1.nickname, cpu_results_1.benchmark_type, cpu_results_1.program_name, cpu_results_1.program_version, cpu_results_1.units, cpu_results_1.cpu_affinity, cpu_results_1.processes, cpu_results_1.threads
        ), max_avg_throughput_agg AS (
         SELECT avg_throughput_agg.nickname,
            avg_throughput_agg.benchmark_type,
            avg_throughput_agg.program_name,
            avg_throughput_agg.program_version,
            avg_throughput_agg.units,
            avg_throughput_agg.cpu_affinity,
            max(avg_throughput_agg.avg_throughput) AS max_avg_throughput
           FROM avg_throughput_agg
          GROUP BY avg_throughput_agg.nickname, avg_throughput_agg.benchmark_type, avg_throughput_agg.program_name, avg_throughput_agg.program_version, avg_throughput_agg.units, avg_throughput_agg.cpu_affinity
        ), avg_throughput_agg_config AS (
         SELECT avg_throughput_agg.nickname,
            avg_throughput_agg.benchmark_type,
            avg_throughput_agg.program_name,
            avg_throughput_agg.program_version,
            avg_throughput_agg.units,
            avg_throughput_agg.cpu_affinity,
            avg_throughput_agg.processes,
            avg_throughput_agg.threads,
            avg_throughput_agg.avg_throughput
           FROM avg_throughput_agg
             JOIN max_avg_throughput_agg ON avg_throughput_agg.avg_throughput = max_avg_throughput_agg.max_avg_throughput AND avg_throughput_agg.nickname = max_avg_throughput_agg.nickname AND avg_throughput_agg.benchmark_type = max_avg_throughput_agg.benchmark_type AND avg_throughput_agg.program_name = max_avg_throughput_agg.program_name AND avg_throughput_agg.program_version = max_avg_throughput_agg.program_version AND avg_throughput_agg.units = max_avg_throughput_agg.units AND avg_throughput_agg.cpu_affinity = max_avg_throughput_agg.cpu_affinity
        )
 SELECT cpu_results.nickname,
	cpu_results.run_date,
	cpu_results.cpu_model,
    cpu_results.benchmark_type,
    cpu_results.program_name,
    cpu_results.program_version,
    cpu_results.units,
    cpu_results.cpu_affinity,
    cpu_results.processes,
    cpu_results.threads,
    cpu_results.usercpu,
    cpu_results.syscpu,
    cpu_results.elapsed,
    cpu_results.maxrss,
    cpu_results.cpu_energy,
    cpu_results.ram_energy,
    cpu_results.repeatnum
   FROM cpu_results
     JOIN avg_throughput_agg_config ON cpu_results.nickname = avg_throughput_agg_config.nickname AND cpu_results.benchmark_type = avg_throughput_agg_config.benchmark_type AND cpu_results.program_name = avg_throughput_agg_config.program_name AND cpu_results.program_version = avg_throughput_agg_config.program_version AND cpu_results.units = avg_throughput_agg_config.units AND cpu_results.cpu_affinity = avg_throughput_agg_config.cpu_affinity AND cpu_results.processes = avg_throughput_agg_config.processes AND cpu_results.threads = avg_throughput_agg_config.threads;

ALTER TABLE public.cpu_results_best_avg_throughput
    OWNER TO benchmarking;


