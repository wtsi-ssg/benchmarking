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
