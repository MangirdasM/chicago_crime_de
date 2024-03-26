import datetime
import os

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.google.cloud.operators.dataproc import (
    ClusterGenerator, DataprocCreateClusterOperator, DataprocSubmitJobOperator)
from google.cloud import storage
from airflow.operators.bash import BashOperator

REGION = "europe-central2"
ZONE = "europe-central2-a"
CLUSTER_NAME = "dataproc-cluster"


AIRFLOW_HOME = os.environ.get("AIRFLOW_HOME", "/opt/airflow/")
PYSPARK_MAIN_FILE = "spark_transformation.py"
PYSPARK_MAIN_FILE_PATH = os.path.join(AIRFLOW_HOME, PYSPARK_MAIN_FILE)
SPARK_BQ_JAR = "spark-bigquery-latest_2.12.jar"
SPARK_BQ_JAR_PATH = os.path.join(AIRFLOW_HOME, SPARK_BQ_JAR)

JAR_URL = "https://storage.googleapis.com/spark-lib/bigquery/spark-3.5-bigquery-0.36.1.jar"

PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
BUCKET = os.environ.get("GCP_GCS_BUCKET")
BIGQUERY_DATASET = os.environ.get("BIGQUERY_DATASET", 'chicago_crime_dataset')



CLUSTER_GENERATOR_CONFIG = ClusterGenerator(
            project_id=PROJECT_ID,
            zone=ZONE,
            master_machine_type="n1-standard-4",
            idle_delete_ttl=900,                    
            master_disk_size=500,
            num_masters=1, # single node cluster
            num_workers=0,                     
        ).make()


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


default_args = {
    "owner": "airflow",
    "start_date": datetime.datetime.now(),
    "depends_on_past": False,
    "retries": 1,
}


with DAG(
    dag_id="data_crime_process_dag",
    schedule_interval="@once",
    default_args=default_args
) as dag:
    
    download_connector_jar_task = BashOperator(
        task_id="download_connector_jar_task",
        bash_command=f"wget -O {AIRFLOW_HOME}/spark-3.5-bigquery-0.36.1.jar {JAR_URL}"
    )
    
    # upload_pyspark_script = PythonOperator(
    #     task_id="upload_pyspark_script",
    #     python_callable=upload_to_gcs,
    #     op_kwargs={
    #         "local_file": PYSPARK_MAIN_FILE_PATH,
    #         "bucket": BUCKET,
    #     },
    # )

    upload_jar = PythonOperator(
        task_id="upload_jar",
        python_callable=upload_to_gcs,
        op_kwargs={
                "bucket": BUCKET,
                "object_name": f"connector/spark-3.5-bigquery-0.36.1.jar",
                "local_file": f"{AIRFLOW_HOME}/spark-3.5-bigquery-0.36.1.jar",
            },
    )

    create_cluster_operator_task = DataprocCreateClusterOperator(
        task_id='create_dataproc_cluster',
        cluster_name=CLUSTER_NAME,
        project_id=PROJECT_ID,
        region=REGION,
        cluster_config=CLUSTER_GENERATOR_CONFIG
    )
    
    # pyspark_task = DataprocSubmitJobOperator(
    #     
    # )
    

    download_connector_jar_task >> upload_jar >> create_cluster_operator_task