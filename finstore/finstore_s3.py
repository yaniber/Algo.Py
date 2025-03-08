# finstore_s3.py

import os
import boto3
import pandas as pd
from io import BytesIO
from cachetools import LRUCache
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

class S3Adapter:
    """
    Minimal S3 adapter for storing/fetching data from LocalStack or AWS S3.
    Reads credentials and endpoint info from environment variables.
    """

    def __init__(self, bucket_name="my-ohlcv-bucket", cache_size=128):
        self.bucket_name = bucket_name
        self.cache = LRUCache(maxsize=cache_size)

        # Pull config from environment
        endpoint_url = os.environ.get("S3_ENDPOINT_URL")  # e.g. http://localstack:4566
        aws_access_key_id = os.environ.get("AWS_ACCESS_KEY_ID", "test")
        aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY", "test")
        region_name = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

        self.s3 = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """
        Ensures the S3 bucket exists. If using LocalStack, the bucket won't persist by default,
        so we create it on startup.
        """
        existing_buckets = [b['Name'] for b in self.s3.list_buckets().get('Buckets', [])]
        if self.bucket_name not in existing_buckets:
            self.s3.create_bucket(Bucket=self.bucket_name)
            print(f"Created bucket '{self.bucket_name}' on {self.s3.meta.endpoint_url}.")

    def store_symbol(
        self,
        market_name: str,
        timeframe: str,
        symbol: str,
        df: pd.DataFrame,
        append: bool = True
    ):
        """
        Store (or append) a symbol’s OHLCV data as a Parquet file in S3.

        Key structure:
          {market_name}/{timeframe}/{symbol}/ohlcv_data.parquet
        """
        s3_key = f"{market_name}/{timeframe}/{symbol}/ohlcv_data.parquet"

        if append:
            # If we want to append, first attempt to load existing data
            existing_df = self._download_parquet_if_exists(s3_key)
            if existing_df is not None and not existing_df.empty:
                df = pd.concat([existing_df, df], ignore_index=True)
                df.drop_duplicates(subset=['timestamp'], inplace=True)

        # Upload
        buffer = BytesIO()
        df.to_parquet(buffer, index=False, compression='snappy')
        buffer.seek(0)
        self.s3.put_object(Bucket=self.bucket_name, Key=s3_key, Body=buffer.read())
        print(f"Stored {len(df)} rows to s3://{self.bucket_name}/{s3_key}")

    def fetch_symbol(
        self,
        market_name: str,
        timeframe: str,
        symbol: str
    ) -> pd.DataFrame:
        """
        Fetch the Parquet file for a symbol.
        Returns an empty DataFrame if not found.
        """
        s3_key = f"{market_name}/{timeframe}/{symbol}/ohlcv_data.parquet"

        # Check cache
        if s3_key in self.cache:
            return self.cache[s3_key]

        df = self._download_parquet_if_exists(s3_key)
        if df is None:
            return pd.DataFrame()  # If not found

        self.cache[s3_key] = df
        return df

    def delete_symbol(
        self,
        market_name: str,
        timeframe: str,
        symbol: str
    ):
        """
        Delete the symbol’s data from S3 (if it exists).
        """
        s3_key = f"{market_name}/{timeframe}/{symbol}/ohlcv_data.parquet"
        try:
            self.s3.delete_object(Bucket=self.bucket_name, Key=s3_key)
            print(f"Deleted s3://{self.bucket_name}/{s3_key}")
        except self.s3.exceptions.NoSuchKey:
            pass

    def _download_parquet_if_exists(self, key: str) -> pd.DataFrame or None:
        """
        Download a Parquet file from S3 if it exists, else return None.
        """
        try:
            response = self.s3.get_object(Bucket=self.bucket_name, Key=key)
            buffer = BytesIO(response['Body'].read())
            df = pd.read_parquet(buffer)
            return df
        except self.s3.exceptions.NoSuchKey:
            return None
        except Exception as e:
            print(f"Error reading {key} from S3: {e}")
            return None
