"""arrivalytica daily pipeline.

Every day at 11:00 AM (America/New_York):
    1. extract_prices — pull all configured routes into today's bronze partition
    2. dbt_build     — rebuild the warehouse models and run all data tests

Each task retries twice, 5 minutes apart, before the run is marked failed.

catchup=False: if the machine was asleep at 11:00, the most recent missed
run fires once on wake — no pile-up of historical backfills.
"""

from datetime import timedelta

import pendulum
from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT = "/opt/airflow/arrivalytica"

with DAG(
    dag_id="arrivalytica_daily",
    description="Daily flight price pull -> dbt build + tests",
    schedule="0 11 * * *",
    start_date=pendulum.datetime(2026, 8, 17, tz="America/New_York"),
    catchup=False,
    default_args={
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
    },
    tags=["arrivalytica"],
) as dag:

    extract_prices = BashOperator(
        task_id="extract_prices",
        bash_command=(
            f"cd {PROJECT} && "
            f"PYTHONPATH={PROJECT}/src python -m flight_tracker.extract"
        ),
    )

    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=f"cd {PROJECT}/dbt && dbt build --profiles-dir .",
    )

    extract_prices >> dbt_build
