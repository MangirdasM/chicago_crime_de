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
PYSPARK_MAIN_FILE = "/dags/spark/data_transformations.py"
PYSPARK_MAIN_FILE_PATH = os.path.join(AIRFLOW_HOME, PYSPARK_MAIN_FILE)
SPARK_BQ_JAR = "spark-bigquery-latest_2.12.jar"
SPARK_BQ_JAR_PATH = os.path.join(AIRFLOW_HOME, SPARK_BQ_JAR)

BQ_JAR_URL = "https://github.com/GoogleCloudDataproc/spark-bigquery-connector/releases/download/0.37.0/spark-bigquery-with-dependencies_2.12-0.37.0.jar"
GCS_JAR_URL = "https://storage.googleapis.com/hadoop-lib/gcs/gcs-connector-latest-hadoop3.jar"

PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
BUCKET = os.environ.get("GCP_GCS_BUCKET")
BIGQUERY_DATASET = os.environ.get("BIGQUERY_DATASET", 'chicago_crime_dataset')
JOB_FILE_URI = ""



CLUSTER_GENERATOR_CONFIG = ClusterGenerator(
            project_id=PROJECT_ID,
            zone=ZONE,
            master_machine_type="n1-standard-4",
            idle_delete_ttl=900,                    
            master_disk_size=500,
            num_masters=1, # single node cluster
            num_workers=0,  
            optional_components=["JUPYTER"],
            enable_component_gateway=True                 
        ).make()

PYSPARK_JOB = {
    "reference": {"project_id": PROJECT_ID},
    "placement": {"cluster_name": CLUSTER_NAME},
    "pyspark_job": {"main_python_file_uri": JOB_FILE_URI},
}


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
    
    download_BQ_connector_jar_task = BashOperator(
        task_id="download_BQ_connector_jar_task",
        bash_command=f"wget -O {AIRFLOW_HOME}/spark-3.5-bigquery-0.36.1.jar {BQ_JAR_URL}"
    )

    download_gcs_connector_jar_task = BashOperator(
        task_id="download_GCS_connector_jar_task",
        bash_command=f"wget -O {AIRFLOW_HOME}/gcs-connector-latest-hadoop3.jar {GCS_JAR_URL}"
    )
    
    upload_pyspark_script = PythonOperator(
        task_id="upload_pyspark_script",
        python_callable=upload_to_gcs,
        op_kwargs={
            "local_file": f"{AIRFLOW_HOME}/{PYSPARK_MAIN_FILE}",
            "bucket": BUCKET,
            "object_name": "scripts/data_transformations.py",
        },
    )

    upload_BQ_jar = PythonOperator(
        task_id="upload_BQ_jar",
        python_callable=upload_to_gcs,
        op_kwargs={
                "bucket": BUCKET,
                "object_name": f"connector/spark-3.5-bigquery-0.36.1.jar",
                "local_file": f"{AIRFLOW_HOME}/spark-3.5-bigquery-0.36.1.jar",
            },
    )

    upload_GCS_jar = PythonOperator(
        task_id="upload_GCS_jar",
        python_callable=upload_to_gcs,
        op_kwargs={
                "bucket": BUCKET,
                "object_name": f"connector/gcs-connector-latest-hadoop3.jar",
                "local_file": f"{AIRFLOW_HOME}/gcs-connector-latest-hadoop3.jar",
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
    


    download_BQ_connector_jar_task >> upload_BQ_jar
    download_gcs_connector_jar_task >> upload_GCS_jar
    [upload_BQ_jar, upload_GCS_jar] >> upload_pyspark_script >> create_cluster_operator_task