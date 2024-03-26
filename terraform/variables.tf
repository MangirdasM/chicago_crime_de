locals {
  data_lake_bucket = "dtc_data_lake"
}

variable "project" {
  description = "Project name"
  default     = "chicago-crime-de-418413"
}

variable "region" {
  description = "Region"
  #Update the below to your desired region
  default     = "europe-west4"
}

variable "location" {
  description = "Project Location"
  #Update the below to your desired location
  default     = "EU"
}

variable "bq_dataset_name" {
  description = "My BigQuery Dataset Name"
  #Update the below to what you want your dataset to be called
  default     = "chicago_crime_dataset"
}

variable "gcs_bucket_name" {
  description = "My Storage Bucket Name"
  #Update the below to a unique bucket name
  default     = "chicago_crime_data"
}

variable "gcs_storage_class" {
  description = "Bucket Storage Class"
  default     = "STANDARD"
}