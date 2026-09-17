"""AML batch pipeline DAG."""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "aml-team",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="aml_batch_pipeline",
    default_args=default_args,
    description="Batch pipeline: generate → load bronze → dbt build (models + tests + snapshots)",
    schedule="*/30 * * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["aml", "batch", "dbt"],
) as dag:

    generate_settlements = BashOperator(
        task_id="generate_settlements",
        bash_command=(
            "cd /opt/airflow && python -m"
            " mock_data_sources.mock_batch_settlements.generate_settlement_file"
        ),
    )

    load_bronze = BashOperator(
        task_id="load_to_bronze",
        bash_command="cd /opt/airflow && python -m loaders.load_to_bronze",
    )

    load_settlements = BashOperator(
        task_id="load_settlements",
        bash_command="cd /opt/airflow && python -m loaders.load_settlements",
    )

    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command="cd /opt/airflow/dbt_banking && dbt deps && dbt build",
    )

    generate_settlements >> [load_bronze, load_settlements] >> dbt_build