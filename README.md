# Market Mind Project

## Overview
The **Market Mind Project** is an end-to-end data pipeline that extracts financial market data from the **Alpha Vantage API**, processes it using **AWS Lambda and AWS Glue**, and stores it in **Amazon S3** for further analysis. This pipeline enables efficient data collection, transformation, and storage for financial insights.

## Architecture
The pipeline consists of the following key components:

1. **AWS Lambda Function:**
   - Fetches real-time stock data from **Alpha Vantage API**.
   - Saves the extracted data as **CSV files** in an S3 bucket (`market-mind-project/raw_data/stocks`).

2. **AWS Glue ETL Jobs:**
   - **Raw Data Processing:** Reads multiple stock CSV files from S3, adds the stock name as an additional column, and merges them into a single dataset.
   - **Processed Data Storage:** Saves the transformed data back to **S3 (`market-mind-project/processed_data/stocks`)** in **Parquet format** for optimized querying and storage.

## Folder Structure
```
📂 Market-Mind-Project
├── 📂 lambda_function                     # AWS Lambda function code
│   ├── lambda_function.py                 # Fetches stock data from Alpha Vantage
├── 📂 glue_jobs                           # AWS Glue ETL Jobs
│   ├── process_econ_indicators_data.py    # Glue Job for processing raw economic indicators data
│   ├── process_stock_data.py              # Glue Job for processing raw stock data
│   ├── process_top_gainers_data.py        # Glue Job for processing raw top gainers data
│   ├── process_crypto_data.py             # Glue Job for processing raw crypto data
├── README.md                              # Project documentation
```

## Setup & Deployment
### 1. AWS Lambda Function
1. Create an **AWS Lambda function** in the AWS console.
2. Upload the **`lambda_function.py`** script.
3. Set environment variables:
   - `API_KEY`: Alpha Vantage API Key
   - `S3_BUCKET`: `market-mind-project`
   - `S3_PREFIX`: `raw_data/stocks`
4. Schedule the Lambda function to run at regular intervals using **Amazon EventBridge (CloudWatch Rules)**.

### 2. AWS Glue ETL Jobs
1. Create a **Glue Job** in the AWS Glue console.
2. Upload the `process_stock_data.py` script.
3. Set the input S3 path (`s3://market-mind-project/raw_data/stocks/`).
4. Set the output S3 path (`s3://market-mind-project/processed_data/stocks/`).
5. Run the Glue job manually or schedule it.
