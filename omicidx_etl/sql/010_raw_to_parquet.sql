--------
--
-- GEO Parquet Files
--
--------

copy (
    select *
    from read_parquet('r2://omicidx/geo/raw/gse_with_rna_seq_counts.parquet')
    order by accession
) to 'r2://omicidx/geo/parquet/geo_series_with_rnaseq_counts.parquet' (format parquet, compression zstd);

select count(*) from read_parquet('r2://omicidx/geo/parquet/geo_series_with_rnaseq_counts.parquet');

copy (
    select *
    from read_ndjson_auto('r2://omicidx/geo/raw/gpl/**/*.ndjson.gz')
    order by accession
) to 'r2://omicidx/geo/parquet/geo_platforms.parquet' (format parquet, compression zstd);


select count(*) from read_parquet('r2://omicidx/geo/parquet/geo_platforms.parquet');

copy (
    select *
    from read_ndjson_auto('r2://omicidx/geo/raw/gse/**/*.ndjson.gz')
    order by accession
) to 'r2://omicidx/geo/parquet/geo_series.parquet' (format parquet, compression zstd);


select count(*) from read_parquet('r2://omicidx/geo/parquet/geo_series.parquet');

copy (
    select *
    from read_ndjson_auto('r2://omicidx/geo/raw/gsm/**/*.ndjson.gz')
    order by accession
) to 'r2://omicidx/geo/parquet/geo_samples.parquet' (format parquet, compression zstd);


select count(*) from read_parquet('r2://omicidx/geo/parquet/geo_samples.parquet');

--------
--
-- SRA Parquet Files
--
--------

copy (
    select *
    from read_csv_auto(
            'https://ftp.ncbi.nlm.nih.gov/sra/reports/Metadata/SRA_Accessions.tab',
            nullstr = '-'
        )
) to 'r2://omicidx/sra/parquet/sra_accessions.parquet' (format parquet, compression zstd);

select count(*) from read_parquet('r2://omicidx/sra/parquet/sra_accessions.parquet');

copy (
    select *
    from read_parquet('r2://omicidx/sra/raw/run/**/*parquet')
    order by accession
) to 'r2://omicidx/sra/parquet/sra_runs.parquet' (format parquet, compression zstd);


select count(*) from read_parquet('r2://omicidx/sra/parquet/sra_runs.parquet');

copy (
    select *
    from read_parquet('r2://omicidx/sra/raw/experiment/**/*parquet')
    order by accession
) to 'r2://omicidx/sra/parquet/sra_experiments.parquet' (format parquet, compression zstd);


select count(*) from read_parquet('r2://omicidx/sra/parquet/sra_experiments.parquet');

copy (
    select *
    from read_parquet('r2://omicidx/sra/raw/sample/**/*parquet')
    order by accession
) to 'r2://omicidx/sra/parquet/sra_samples.parquet' (format parquet, compression zstd);


select count(*) from read_parquet('r2://omicidx/sra/parquet/sra_samples.parquet');

copy (
    select *
    from read_parquet('r2://omicidx/sra/raw/study/**/*parquet')
    order by accession
) to 'r2://omicidx/sra/parquet/sra_studies.parquet' (format parquet, compression zstd);


select count(*) from read_parquet('r2://omicidx/sra/parquet/sra_studies.parquet');

--------
--
-- BioProject and BioSample Parquet Files
--
--------


copy (
    select *
    from read_ndjson_auto(
            'r2://omicidx/biosample/biosample/raw/bioproject/raw/bioproject.jsonl.gz',
            maximum_object_size = 1000000000
        )
) to 'r2://omicidx/bioproject/parquet/bioprojects.parquet' (format parquet, compression zstd);


select count(*) from read_parquet('r2://omicidx/bioproject/parquet/bioprojects.parquet');

copy (
    select *
    from read_ndjson_auto(
            'r2://omicidx/biosample/biosample/raw/biosample/raw/biosample.jsonl.gz',
            maximum_object_size = 1000000000
        )
) to 'r2://omicidx/biosample/parquet/biosamples.parquet' (format parquet, compression zstd);

select count(*) from read_parquet('r2://omicidx/biosample/parquet/biosamples.parquet');