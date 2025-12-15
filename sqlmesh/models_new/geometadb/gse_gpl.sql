
SELECT DISTINCT
    accession AS gpl,
    UNNEST(series_id) AS gse
FROM raw.src_geo_platforms
