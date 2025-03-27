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
input_path = "s3://market-mind-project/raw_data/economic_indicators/"
output_path = "s3://market-mind-project/processed_data/economic_indicators/"
bucket_name = "market-mind-project"
output_prefix = "processed_data/economic_indicators/"  # S3 key prefix
temp_output_path = output_path + "temp_output/"  # Temporary folder for writing data

# Initialize S3 client
s3 = boto3.client("s3")

# Function to delete existing files in an S3 folder
def delete_s3_folder(bucket, prefix):
    objects_to_delete = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    
    if "Contents" in objects_to_delete:
        delete_keys = [{"Key": obj["Key"]} for obj in objects_to_delete["Contents"]]
        s3.delete_objects(Bucket=bucket, Delete={"Objects": delete_keys})
        print(f"Deleted {len(delete_keys)} files from {prefix}")

# Delete existing output files
delete_s3_folder(bucket_name, output_prefix)

# Read raw economic indicator data from S3
df = spark.read.option("header", True).csv(input_path)

# Add a column with the full file path
df = df.withColumn("file_path", input_file_name())

# Assign indicator names based on file paths
df = df.withColumn(
    "indicator",
    when(df["file_path"].contains("treasury"), "Treasury Yield")
    .when(df["file_path"].contains("federal"), "Federal Funds Rate")
    .when(df["file_path"].contains("cpi"), "CPI")
    .otherwise("Unknown")  # Default value for unmatched cases
)

df = df.drop("file_path")

# Convert to DynamicFrame for Glue
dyf = DynamicFrame.fromDF(df, glueContext, "indicators_data")

# Convert DynamicFrame to DataFrame
df_final = dyf.toDF()

# Coalesce into a single partition to ensure only one output file
df_final = df_final.coalesce(1)

# Write to a temporary folder in S3
df_final.write.mode("overwrite").parquet(temp_output_path)

# Wait for the file to appear in S3 (sometimes needed in Glue)
time.sleep(5)

# List objects in the temporary output folder
objects = s3.list_objects_v2(Bucket=bucket_name, Prefix="processed_data/economic_indicators/temp_output/")

# Find the Parquet file
parquet_file_key = None
if "Contents" in objects:
    for obj in objects["Contents"]:
        if obj["Key"].endswith(".parquet"):
            parquet_file_key = obj["Key"]
            break

if parquet_file_key:
    # Define the fixed filename
    fixed_filename = "processed_data/economic_indicators/final_economic_indicators.parquet"

    # Copy the file to the desired location with the fixed name
    s3.copy_object(
        Bucket=bucket_name,
        CopySource={"Bucket": bucket_name, "Key": parquet_file_key},
        Key=fixed_filename
    )

    # Delete the temporary files
    delete_s3_folder(bucket_name, "processed_data/economic_indicators/temp_output/")
    
    print(f"File successfully renamed to: s3://{bucket_name}/{fixed_filename}")

# Commit the Glue job
job.commit()
