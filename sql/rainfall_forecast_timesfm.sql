SELECT
  forecast_timestamp,
  forecast_value AS predicted_rainfall
FROM AI.FORECAST(
  MODEL `bigquery-public-data.ml_datasets.timesfm_model`,
  (
    SELECT
      timestamp,
      rainfall_mm
    FROM `PROJECT_ID.chennai_flood.rainfall_history`
    ORDER BY timestamp
  ),
  STRUCT(7 AS horizon, 0.8 AS confidence_level)
)
ORDER BY forecast_timestamp;
