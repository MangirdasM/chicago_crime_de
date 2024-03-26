from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.utils.dates import days_ago
import os
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from google.cloud import storage
from airflow.providers.google.cloud.operators.bigquery import BigQueryCreateExternalTableOperator

import pyarrow.csv as pv
import pyarrow.parquet as pq
import logging


AIRFLOW_HOME = os.environ.get("AIRFLOW_HOME", "/opt/airflow/")
OUTPUT_FILE_TEMPLATE = AIRFLOW_HOME + '/output.csv.gz'

PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
BUCKET = os.environ.get("GCP_GCS_BUCKET")
BIGQUERY_DATASET = os.environ.get("BIGQUERY_DATASET", 'chicago_crime_dataset')




datasets_links = [
    'https://data.cityofchicago.org/resource/kf95-mnd6.csv?\$limit=300000',
    'https://data.cityofchicago.org/resource/d62x-nvdr.csv?\$limit=300000',
    'https://data.cityofchicago.org/resource/3i3m-jwuy.csv?\$limit=300000',
    'https://data.cityofchicago.org/resource/w98m-zvie.csv?\$limit=300000',
    'https://data.cityofchicago.org/resource/qzdf-xmn8.csv?\$limit=300000']


def format_to_parquet(src_file):
    if not src_file.endswith('.csv'):
        logging.error("Can only accept source files in CSV format, for the moment")
        return
    table = pv.read_csv(src_file)
    pq.write_table(table, src_file.replace('.csv', '.parquet'))

def upload_to_gcs(bucket, object_name, local_file):
    """
    Ref: https://cloud.google.com/storage/docs/uploading-objects#storage-upload-object-python
    :param bucket: GCS bucket name
    :param object_name: target path & file-name
    :param local_file: source path & file-name
    :return:
    """
    # WORKAROUND to prevent timeout for files > 6 MB on 800 kbps upload speed.
    # (Ref: https://github.com/googleapis/python-storage/issues/74)
    storage.blob._MAX_MULTIPART_SIZE = 5 * 1024 * 1024  # 5 MB
    storage.blob._DEFAULT_CHUNKSIZE = 5 * 1024 * 1024  # 5 MB
    # End of Workaround

    client = storage.Client()
    bucket = client.bucket(bucket)

    blob = bucket.blob(object_name)
    blob.upload_from_filename(local_file)


with DAG(
    'ingesting_data_bq',
    schedule_interval='@daily',
    start_date=days_ago(1),
    catchup=False
) as dag:
    start = DummyOperator(task_id='start',)
    stop = DummyOperator(task_id='stop')

    for dataset in datasets_links:
        dataset_number = datasets_links.index(dataset)

        download_task = BashOperator(
            task_id=f'download_dataset_{dataset_number}_task',
            bash_command=f"wget -O {AIRFLOW_HOME}/chicago_crime_data_{dataset_number}.csv {dataset}",
        )
        
        format_to_parquet_task = PythonOperator(
            task_id=f"format_to_parquet_dataset_{dataset_number}_task",
            python_callable=format_to_parquet,
            op_kwargs={
                "src_file": f"{AIRFLOW_HOME}/chicago_crime_data_{dataset_number}.csv",
            },
        )
        
        local_to_gcs_task = PythonOperator(
            task_id=f"local_to_gcs_{dataset_number}_task",
            python_callable=upload_to_gcs,
            op_kwargs={
                "bucket": BUCKET,
                "object_name": f"raw/chicago_crime_data_{dataset_number}.parquet",
                "local_file": f"{AIRFLOW_HOME}/chicago_crime_data_{dataset_number}.parquet",
            },
        )

        delete_task = BashOperator(
            task_id=f'delete_dataset_files_{dataset_number}_task',
            bash_command=f"rm {AIRFLOW_HOME}/chicago_crime_data_{dataset_number}.csv \
            rm {AIRFLOW_HOME}/chicago_crime_data_{dataset_number}.parquet",
            )
        
        bigquery_external_table_task = BigQueryCreateExternalTableOperator(
            task_id=f"bigquery_external_table_{dataset_number}_task",

            table_resource={
                "tableReference": {
                    "projectId": PROJECT_ID,
                    "datasetId": BIGQUERY_DATASET,
                    "tableId": f"{BIGQUERY_DATASET}_external_table",
                },
                
                "externalDataConfiguration": {
                    "autodetect": "True",
                    "sourceFormat": "PARQUET",
                    "sourceUris": [f"gs://{BUCKET}/raw/*"],
                },
           }
        )
        start >> download_task >> format_to_parquet_task >> local_to_gcs_task >> delete_task >> bigquery_external_table_task >> stop
