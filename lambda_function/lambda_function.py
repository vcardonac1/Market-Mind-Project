import boto3
import pandas as pd
import io
import os
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.econindicators import EconIndicators
from alpha_vantage.alphaintelligence import AlphaIntelligence
from alpha_vantage.commodities import Commodities
from alpha_vantage.cryptocurrencies import CryptoCurrencies
import datetime

API_KEY = 'BTAXTABC946FQAC0'

stocks = ['AAPL', 'MSFT', 'TSLA', 'NVDA', 'AMZN', 'GOOGL', 'META', 'BRK.B', 'JPM', 'V']
cryptos = ["BTC", "ETH", "USDT", "XRP", "ADA", "SOL", "DOGE", "DOT", "LTC", "BCH"]

# Bucket datails
S3_BUCKET = "market-mind-project"
S3_FOLDER_RAW = 'raw_data'
S3_FOLDER_STOCK = f"{S3_FOLDER_RAW}/stocks"
S3_FOLDER_COMM = f"{S3_FOLDER_RAW}/commodities"
S3_FOLDER_ECON = f"{S3_FOLDER_RAW}/economic_indicators"
S3_FOLDER_TOP = f"{S3_FOLDER_RAW}/top_gainers"
S3_FOLDER_CRYPTO = f"{S3_FOLDER_RAW}/crypto"

s3 = boto3.client('s3')

def save_df_to_s3(df, bucket, key):
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=csv_buffer.getvalue(),
        ContentType="text/csv"
    )
    print(f"File saved to S3: s3://{bucket}/{key}")

def getStockData():
    ts = TimeSeries(key=API_KEY, output_format='pandas')

    for stock in stocks:
        data, meta_data = ts.get_daily(symbol=stock, outputsize='full')
        data.reset_index(inplace=True)
        data.columns = ["date", "open", "high", "low", "close", "volume"]
        data = data[data['date']>'2020-01-01']
        
        # Save to S3
        file_name = stock + '.csv'
        S3_KEY = f"{S3_FOLDER_STOCK}/{file_name}"
        save_df_to_s3(data, S3_BUCKET, S3_KEY)

def getCommodities():
    commodities = Commodities(key=API_KEY, output_format="pandas")

    data_natgas, meta_data = commodities.get_natural_gas(interval='monthly')
    data_aluminum, meta_data = commodities.get_aluminum(interval='monthly')
    data_brent, meta_data = commodities.get_brent(interval='monthly')
    data_coffee, meta_data = commodities.get_coffee(interval='monthly')
    data_copper, meta_data = commodities.get_copper(interval='monthly')
    data_corn, meta_data = commodities.get_corn(interval='monthly')
    data_cotton, meta_data = commodities.get_cotton(interval='monthly')
    data_sugar, meta_data = commodities.get_sugar(interval='monthly')
    data_wheat, meta_data = commodities.get_wheat(interval='monthly')
    data_wti, meta_data = commodities.get_wti(interval='monthly')
    
    commoditiesD = {
        "natgas": data_natgas,
        "aluminum": data_aluminum,
        "brent": data_brent,
        "coffee": data_coffee,
        "copper": data_copper,
        "corn": data_corn,
        "cotton": data_cotton,
        "sugar": data_sugar,
        "wheat": data_wheat,
        "wti": data_wti
    }
    
    for name, df in commoditiesD.items():   
        df.reset_index(inplace=True, drop=True)
        df = df[df['date']>'2020-01-01']
           
        # Save to S3
        file_name = name + '.csv'
        S3_KEY = f"{S3_FOLDER_COMM}/{file_name}"
        save_df_to_s3(df, S3_BUCKET, S3_KEY)
        
def getEconIndicators():
    econ = EconIndicators(key=API_KEY, output_format='pandas')

    real_gdp_data, meta_data = econ.get_real_gdp() #year
    inflation_data, meta_data = econ.get_inflation() #year
    cpi_data, meta_data = econ.get_cpi() #month
    real_gdp_per_capita_data, meta_data = econ.get_real_gdp_per_capita() #quarterly

    econIndicatorsArray = {
        "real_gdp": real_gdp_data,
        "inflation": inflation_data,
        "cpi": cpi_data,
        "real_gdp_per_capita": real_gdp_per_capita_data
    }
    
    for name, df in econIndicatorsArray.items():
        df.reset_index(inplace=True, drop=True)      
        df = df[df['date']>='2020-01-01']

        # Save to S3
        file_name = name + '.csv'
        S3_KEY = f"{S3_FOLDER_ECON}/{file_name}"
        save_df_to_s3(df, S3_BUCKET, S3_KEY)

def getTopGainers():
    ai = AlphaIntelligence(key=API_KEY, output_format='json')
    market_movers = ai.get_top_gainers()

    market_movers_df = market_movers[0]
    
    # Save to S3
    file_name = 'top_gainers.csv'
    S3_KEY = f"{S3_FOLDER_TOP}/{file_name}"
    save_df_to_s3(market_movers_df, S3_BUCKET, S3_KEY)
    
def getCryptoData():
    cc = CryptoCurrencies(key=API_KEY, output_format='pandas')

    for s in cryptos:
        data, meta_data = cc.get_digital_currency_daily(symbol=s, market='USD')
        data.reset_index(inplace=True)
        data.columns = ["date", "open", "high", "low", "close", "volume"]
        
        # Save to S3
        file_name = s + '.csv'
        S3_KEY = f"{S3_FOLDER_CRYPTO}/{file_name}"
        save_df_to_s3(data, S3_BUCKET, S3_KEY)

def lambda_handler(event, context):
    today = datetime.datetime.utcnow().day    
    if today == 2:
        getEconIndicators() # monthly

    getCryptoData() # daily
    getStockData() # daily
    getTopGainers() # daily
    
    return {
        "statusCode": 200,
        "body": f"Data saved successfully to s3://{S3_BUCKET}/{S3_FOLDER_RAW}"
    }
