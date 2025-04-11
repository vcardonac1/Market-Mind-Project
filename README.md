# Market Mind Project

## Overview  
The Market Mind Project is an end-to-end data pipeline designed to extract, process, store, and visualize financial market data. It fetches data from the Alpha Vantage API, processes it using AWS Lambda and AWS Glue, and stores it in Amazon S3. The processed data is then used to power a real-time interactive dashboard, hosted on an EC2 instance and built with Streamlit, enabling users to dynamically analyze financial market trends.

## Technologies Used  
- **AWS Lambda** – Fetches financial data from the Alpha Vantage API.
- **AWS Glue** – Cleans and transforms raw data.
- **Amazon S3** – Stores both raw and processed data.
- **EC2** – Hosts the interactive dashboard.
- **Streamlit** – Provides a real-time data visualization interface.

## How It Works  
1. **Data Extraction**: AWS Lambda periodically fetches stock, crypto currency, and economic indicator data from the Alpha Vantage API and saves it to S3.
2. **Data Transformation**: AWS Glue ETL jobs process and clean the data, consolidating it into structured tables.
3. **Storage**: The processed data is stored in Amazon S3 in Parquet format for optimized querying.
4. **Visualization**: An EC2-hosted Streamlit application loads and visualizes the data, allowing users to explore market trends in real time.

## Architecture
The pipeline consists of the following key components:

1. **AWS Lambda Function:**
   - Fetches real-time stock data from **Alpha Vantage API**.
   - Saves the extracted data as **CSV files** in an S3 bucket (`market-mind-project/raw_data/stocks`).

2. **AWS Glue ETL Jobs:**
   - **Raw Data Processing:** Reads multiple stock CSV files from S3, adds the stock name as an additional column, and merges them into a single dataset.
   - **Processed Data Storage:** Saves the transformed data back to **S3 (`market-mind-project/processed_data/stocks`)** in **Parquet format** for optimized querying and storage.

3. **Streamlit App:**
   - Loads and visualizes the processed *stock/crypto/economic indicators/top gainers* data stored in **Parquet format** from S3.
   - Provides interactive charts and metrics for exploring *stock/crypto/economic indicators/top gainers* performance over time.

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
├── 608-dashboard.py                       # Streamlit code for the dashboard
├── requirements.txt                       # Required libraries to execute the Streamlit code
├── runtime.txt                            # Runtime for the Streamlit Dashboard
├── background.png                         # Background image for the dashboard
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

### 3. Dashboard
You can easily deploy this Streamlit dashboard using [Streamlit Community Cloud](https://streamlit.io/cloud). Follow these steps:

1. Fork or clone this repository.
2. Go to [streamlit.io/cloud](https://streamlit.io/cloud) and sign in with your GitHub account.
3. Click on **"New app"**.
4. In the **Repository** dropdown, select your forked repo.
5. In the **File path** field, enter: "608-dashboard.py".
6. Click **"Deploy"**.
