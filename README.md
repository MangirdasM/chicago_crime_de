## About

In this project data from [chicago crime](https://data.cityofchicago.org/) datesets from year 2016 to 2019 is used.

The aim of this project is to create a data pipeline to ingest and process the data and finally visualize this processed data.

## Dashboard

![alt text](dash/analysis.PNG)

## Tools

- Terraform
- Docker
- Google Cloud Storage
- Google BigQuery
- Google Dataproc
- Airflow
- Spark
- Looker studio

## Setup

1. In [Google cloud console](https://console.cloud.google.com/) create a new project.
2. Create a service account with these roles:
    - BigQuery Admin
    - Compute engine service agent
    - Dataproc administrator
    - Storage admin
    - Storage object admin
3. Save service account credentials as json file.
4. Setup .env file in airflow folder
5. Run the terraform commands

        cd terraform
        terraform init
        terraform plan
        terraform apply
6. Start airflow

        cd airflow
        docker compose up
