-- Raw source view: Direct read from GEO series NDJSON files
-- This view captures GEO series that have associated RNA-Seq count data
-- This is an internal view for ETL only - not exposed to end users
MODEL (
    name raw.src_geo_series_with_rnaseq_counts,
    kind VIEW
);

SELECT
    accession::VARCHAR as accession,
FROM
    read_ndjson_auto(@data_root || '/geo/gse_with_rna_seq_counts.jsonl.gz', union_by_name=true)
