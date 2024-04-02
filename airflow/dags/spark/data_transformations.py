import argparse

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql import types


schema  = types.StructType([
    types.StructField('ID', types.StringType(), True), 
    types.StructField('Case Number', types.StringType(), True), 
    types.StructField('Date', types.StringType(), True), 
    types.StructField('Block', types.StringType(), True), 
    types.StructField('IUCR', types.StringType(), True), 
    types.StructField('Description', types.StringType(), True), 
    types.StructField('Primary Type', types.StringType(), True), 
    types.StructField('Location Description', types.StringType(), True), 
    types.StructField('Arrest', types.StringType(), True), 
    types.StructField('Domestic', types.StringType(), True), 
    types.StructField('Beat', types.StringType(), True), 
    types.StructField('District', types.StringType(), True), 
    types.StructField('Ward', types.StringType(), True), 
    types.StructField('Community Area', types.IntegerType(), True), 
    types.StructField('FBI Code', types.StringType(), True), 
    types.StructField('X Coordinate', types.StringType(), True), 
    types.StructField('Y Coordinate', types.StringType(), True), 
    types.StructField('Year', types.StringType(), True), 
    types.StructField('Updated On', types.StringType(), True), 
    types.StructField('Latitude', types.StringType(), True), 
    types.StructField('Longitude', types.StringType(), True), 
    types.StructField('Location', types.StringType(), True), 
    types.StructField('Historical Wards 2003-2015', types.StringType(), True), 
    types.StructField('Zip Codes', types.StringType(), True), 
    types.StructField('Community Areas', types.StringType(), True), 
    types.StructField('Census Tracts', types.StringType(), True), 
    types.StructField('Wards', types.StringType(), True), 
    types.StructField('Boundaries - ZIP Codes', types.StringType(), True), 
    types.StructField('Police Districts', types.StringType(), True), 
    types.StructField('Police Beats', types.StringType(), True)])


spark = SparkSession.builder \
    .master('yarn') \
    .appName('test') \
    .getOrCreate()

spark.conf.set('temporaryGcsBucket', 'dataproc-temp-europe-central2-909036293289-xyutsjfe')
spark.conf.set("spark.sql.debug.maxToStringFields", 1000)
spark.conf.set("viewsEnabled","true")
spark.conf.set("materializationDataset","<dataset>")

df = spark.read \
    .schema(schema) \
    .parquet('gs://dtc_data_lake_chicago-crime-de-418413/raw/*')



print(df.count())
print(df.schema)

df = df \
    .withColumnRenamed('Case Number', 'CaseNumber') \
    .withColumnRenamed('Primary Type', 'Primary_Type') \
    .withColumnRenamed('Location Description', 'Location_Description') \
    .withColumnRenamed('Community Area', 'Community_Area') \
    .withColumnRenamed('FBI Code', 'FBI_Code') \
    .withColumnRenamed('X Coordinate', 'X_Coordinate') \
    .withColumnRenamed('Y Coordinate', 'Y_Coordinate') \
    .withColumnRenamed('Updated On', 'Updated_On') \
    .withColumnRenamed('Zip Codes', 'Zip_Codes') \
    .withColumnRenamed('Community Areas', 'Community_Areas') \
    .withColumnRenamed('Historical Wards 2003-2015', 'Historical_Wards') \
    .withColumnRenamed('Census Tracts', 'Census_Tracts') \
    .withColumnRenamed('Boundaries - ZIP Codes', 'ZIP_Codes_B') \
    .withColumnRenamed('Police Districts', 'Police_Districts') \
    .withColumnRenamed('Police Beats', 'Police_Beats') \

print(df.schema)

df.write.format('com.google.cloud.spark.bigquery') \
  .option('temporaryGcsBucket','dataproc-temp-europe-central2-909036293289-xyutsjfe') \
  .option("table", 'chicago_crime_dataset/crime_output') \
  .save()


        





