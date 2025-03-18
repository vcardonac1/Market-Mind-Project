import sys
import boto3  # Import boto3 for S3 operations
import time  # For waiting for the file to appear in S3
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import input_file_name, when
from awsglue.dynamicframe import DynamicFrame

# Initialize Glue Context
args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Define S3 paths
input_path = "s3://market-mind-project/raw_data/top_gainers/"
output_path = "s3://market-mind-project/processed_data/top_gainers/"
bucket_name = "market-mind-project"
output_prefix = "processed_data/top_gainers/"  # S3 key prefix
temp_output_path = output_path + "temp_output/"  # Temporary folder

# Initialize S3 client
s3 = boto3.client("s3")

# Function to delete existing files in an S3 folder
def delete_s3_folder(bucket, prefix):
    objects_to_delete = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    
    if "Contents" in objects_to_delete:
        delete_keys = [{"Key": obj["Key"]} for obj in objects_to_delete["Contents"]]
        s3.delete_objects(Bucket=bucket, Delete={"Objects": delete_keys})
        print(f"Deleted {len(delete_keys)} files from {output_path}")

# Delete existing output files
delete_s3_folder(bucket_name, output_prefix)

# Read raw data from S3
df = spark.read.option("header", True).csv(input_path)

# Convert to DynamicFrame for Glue
dyf = DynamicFrame.fromDF(df, glueContext, "top_gainers_data")

# Convert DynamicFrame to DataFrame
df_final = dyf.toDF()

# Coalesce into a single partition to ensure only one output file
df_final = df_final.coalesce(1)

# Write to a temporary folder in S3
df_final.write.mode("overwrite").parquet(temp_output_path)

# Wait for the file to appear in S3 (sometimes needed in Glue)
time.sleep(5)

# List objects in the temporary output folder
objects = s3.list_objects_v2(Bucket=bucket_name, Prefix="processed_data/top_gainers/temp_output/")

# Find the Parquet file
parquet_file_key = None
if "Contents" in objects:
    for obj in objects["Contents"]:
        if obj["Key"].endswith(".parquet"):
            parquet_file_key = obj["Key"]
            break

if parquet_file_key:
    # Define the fixed filename
    fixed_filename = "processed_data/top_gainers/final_top_gainers.parquet"

    # Copy the file to the desired location with the fixed name
    s3.copy_object(
        Bucket=bucket_name,
        CopySource={"Bucket": bucket_name, "Key": parquet_file_key},
        Key=fixed_filename
    )

    # Delete the temporary files
    delete_s3_folder(bucket_name, "processed_data/top_gainers/temp_output/")
    
    print(f"File successfully renamed to: s3://{bucket_name}/{fixed_filename}")

# Commit the Glue job
job.commit()
