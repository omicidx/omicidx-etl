-- Bronze staging: Incremental table capturing daily changes for GEO platforms
-- Reads from raw.src_geo_platforms and materializes changes
MODEL (
    name bronze.stg_geo_platforms,
    kind INCREMENTAL_BY_TIME_RANGE (
        time_column (last_update_date)
    ),
    cron '@daily',
    grain accession
);

SELECT
    title::VARCHAR,
    status::VARCHAR,
    submission_date::DATE,
    last_update_date::DATE,
    accession::VARCHAR,
    contact::STRUCT(city VARCHAR, "name" STRUCT("first" VARCHAR, middle VARCHAR, "last" VARCHAR), email VARCHAR, state VARCHAR, address VARCHAR, department VARCHAR, country VARCHAR, web_link VARCHAR, institute VARCHAR, zip_postal_code JSON, phone VARCHAR),
    summary::JSON,
    organism::VARCHAR,
    sample_id::VARCHAR[],
    series_id::VARCHAR[],
    technology::VARCHAR,
    description::VARCHAR,
    distribution::VARCHAR,
    manufacturer::VARCHAR[],
    data_row_count::BIGINT,
    contributor::STRUCT("first" VARCHAR, middle VARCHAR, "last" VARCHAR)[],
    relation::VARCHAR[],
    manufacture_protocol::VARCHAR
FROM
    raw.src_geo_platforms
WHERE
    last_update_date BETWEEN @start_ds AND @end_ds
