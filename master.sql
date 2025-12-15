
 CREATE or replace SECRET minio (
    TYPE s3,
    KEY_ID '',
    SECRET '',
    ENDPOINT 'minio.cancerdatasci.org',
    URL_STYLE 'path',
    REGION 'us-east-1',
    USE_SSL True
);

create schema raw;
use raw;

-- SRA ----------------------------------------------

create or replace view src_sra_accessions as select * from read_parquet('s3://omicidx/sra/raw/accessions/*parquet');

create or replace view src_sra_studies as select * from read_parquet('s3://omicidx/sra/raw/study/**/*parquet');
create or replace view src_sra_samples as select * from read_parquet('s3://omicidx/sra/raw/sample/**/*parquet');   
create or replace view src_sra_runs as select * from read_parquet('s3://omicidx/sra/raw/run/**/*parquet');    
create or replace view src_sra_experiments as select * from read_parquet('s3://omicidx/sra/raw/experiment/**/*parquet');

-- GEO ----------------------------------------------

create or replace view src_geo_series as select * from read_ndjson_auto('s3://omicidx/geo/raw/gse/**/*ndjson.gz');
create or replace view src_geo_samples as select * from read_ndjson_auto('s3://omicidx/geo/raw/gsm/**/*ndjson.gz');
create or replace view src_geo_platforms as select * from read_ndjson_auto('s3://omicidx/geo/raw/gpl/**/*ndjson.gz');
create or replace view src_geo_gse_with_rna_seq_counts as select * from read_ndjson_auto('s3://omicidx/geo/raw/gse_with_rna_seq_counts.jsonl.gz');


-- PUBLICATIONS -------------------------------------

-- create or replace view src_pubmed_metadata as select * from read_parquet('s3://omicidx/pubmed/raw/*parquet');
-- create or replace view src_icite_metadata as select * from read_parquet('s3://omicidx/icite/raw/icite_metadata/*parquet');
-- create or replace view src_icite_citations as select * from read_parquet('s3://omicidx/icite/raw/icite_opencitations/*parquet');
-- create or replace view src_europepmc_references as select * from read_parquet('s3://omicidx/europepmc/raw/*parquet');

-- BIOSAMPLE ----------------------------------------

create or replace view src_bioprojects as select * from read_parquet('s3://omicidx/biosample/raw/bioproject/raw/*parquet');
create or replace view src_biosamples as select * from read_parquet('s3://omicidx/biosample/raw/biosample/raw/*parquet');

create schema geometadb;