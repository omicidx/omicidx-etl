MODEL (
    name bronze.stg_geo_series_with_rnaseq_counts,
    kind INCREMENTAL_BY_UNIQUE_KEY (
        unique_key (accession)
    ),
    cron '@daily',
    grain accession
);

SELECT
    accession::VARCHAR
FROM
    raw.src_geo_series_with_rnaseq_counts;