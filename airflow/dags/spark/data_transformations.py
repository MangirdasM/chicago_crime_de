import argparse

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql import types

parser = argparse.ArgumentParser()
parser.add_argument("--bucket", required=True, type=str)
args = parser.parse_args()

crime_schema  = types.StructType([
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

com_schema  = types.StructType([
    types.StructField('the_geom', types.StringType(), True), 
    types.StructField('PERIMETER', types.StringType(), True), 
    types.StructField('AREA', types.StringType(), True), 
    types.StructField('COMAREA', types.StringType(), True), 
    types.StructField('COMAREA_ID', types.StringType(), True), 
    types.StructField('AREA_NUMBA', types.StringType(), True), 
    types.StructField('COMMUNITY', types.StringType(), True), 
    types.StructField('AREA_NUM_1', types.IntegerType(), True), 
    types.StructField('SHAPE_AREA', types.StringType(), True), 
    types.StructField('SHAPE_LEN', types.StringType(), True)])


def change_location_format(lat, long):
    txt = "{0},{1}".format(lat, long)
    return txt

change_location_format = F.udf(change_location_format, returnType=types.StringType())

spark = SparkSession.builder \
    .master('yarn') \
    .appName('transform_data') \
    .getOrCreate()

spark.conf.set('temporaryGcsBucket', 'dataproc-temp-europe-central2-909036293289-xyutsjfe')
spark.conf.set("spark.sql.debug.maxToStringFields", 1000)
spark.conf.set("viewsEnabled","true")
spark.conf.set("materializationDataset","<dataset>")

crime_df = spark.read \
    .schema(crime_schema) \
    .csv(f'gs://{args.bucket}/raw/crime_data/*')

comm_df = spark.read \
    .schema(com_schema) \
    .csv(f'gs://{args.bucket}/raw/comm_areas/*')


crime_df = crime_df \
    .withColumnRenamed('Case Number', 'case_number') \
    .withColumnRenamed('Primary Type', 'primary_type') \
    .withColumnRenamed('Location Description', 'location_description') \
    .withColumnRenamed('Community Area', 'community_area') \
    .withColumnRenamed('FBI Code', 'FBI_code') \
    .withColumnRenamed('X Coordinate', 'X_coordinate') \
    .withColumnRenamed('Y Coordinate', 'Y_coordinate') \
    .withColumnRenamed('Updated On', 'updated_on') \
    .withColumnRenamed('Zip Codes', 'zip_codes') \
    .withColumnRenamed('Community Areas', 'community_areas') \
    .withColumnRenamed('Historical Wards 2003-2015', 'historical_wards') \
    .withColumnRenamed('Census Tracts', 'census_tracts') \
    .withColumnRenamed('Boundaries - ZIP Codes', 'ZIP_codes_B') \
    .withColumnRenamed('Police Districts', 'police_districts') \
    .withColumnRenamed('Police Beats', 'police_beats')

cond = [crime_df.community_area == comm_df.AREA_NUMBA]

crime_df \
    .withColumn('Location', change_location_format(crime_df.Latitude, crime_df.Longitude)) \
    .withColumn("Date", F.from_unixtime(F.unix_timestamp("Date",'M/d/yyyy h:mm:ss a'),'yyyy-M-d')) \
    .join(comm_df, cond, "inner") \
    .select('ID',"case_number", 'Arrest', 'Domestic', 'IUCR', 'Date', 'primary_type','COMMUNITY', 'Location') \
    .coalesce(1) \
    .write.format('bigquery') \
    .option('temporaryGcsBucket','dataproc-temp-europe-central2-909036293289-xyutsjfe') \
    .option("table", 'chicago_crime_dataset.crime_output') \
    .mode('overwrite') \
    .save()



        





