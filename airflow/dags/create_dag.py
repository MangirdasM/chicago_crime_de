from datetime import datetime
from airflow.utils.dates import days_ago

from airflow import DAG
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryCreateEmptyDatasetOperator,
    BigQueryInsertJobOperator,
)

default_args = {
    "owner": "airflow",
    "start_date": days_ago(1),
    "depends_on_past": False,
    "retries": 1,
}

with DAG(
    dag_id="create_simple_table",
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
) as dag:
    create_dataset_task = BigQueryCreateEmptyDatasetOperator(
        task_id="create_dataset",
        dataset_id="test_dataset",
        location="eu",
    )
    create_simple_table_task = BigQueryInsertJobOperator(
        task_id="create_simple_table",
        configuration={
            "query": {
                "query": "create_bq_table.sql",
                "useLegacySql": False,
            }
        },
    )

create_dataset_task >> create_simple_table_task