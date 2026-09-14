"""AML batch pipeline DAG — runs daily to process settlements and transform data."""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "aml-team",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="aml_batch_pipeline",
    default_args=default_args,
    description="Daily batch pipeline: load settlements → dbt run → dbt snapshot",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["aml", "batch", "dbt"],
) as dag:

    load_settlements = BashOperator(
        task_id="load_settlements",
        bash_command="cd /opt/airflow && python -m loaders.load_settlements",
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="cd /opt/airflow/dbt_banking && dbt run",
    )

    dbt_snapshot = BashOperator(
        task_id="dbt_snapshot",
        bash_command="cd /opt/airflow/dbt_banking && dbt snapshot",
    )

    # Define execution order
    load_settlements >> dbt_run >> dbt_snapshot