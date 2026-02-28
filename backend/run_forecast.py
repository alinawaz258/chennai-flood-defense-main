"""Run BigQuery TimesFM rainfall forecast and return pandas output."""

from backend.app.services.bigquery_service import BigQueryRepository


def main() -> None:
    repo = BigQueryRepository()
    df = repo.forecast_rainfall()
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
