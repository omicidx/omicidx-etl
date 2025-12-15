

SELECT DISTINCT
    accession AS gse,
    UNNEST(sample_id) AS gsm
FROM raw.src_geo_series
