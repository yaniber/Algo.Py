# finstore_s3.py

import os
import boto3
import pandas as pd
from io import BytesIO
from cachetools import LRUCache
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from enum import Enum

class PartitionType(Enum):
    NONE = "none"
    DAILY = "daily"
    MONTHLY = "monthly"

class S3Adapter:
    """
    Minimal S3 adapter for storing/fetching partitioned OHLCV data from a LocalStack or AWS S3 endpoint.
    Reads credentials and endpoint info from environment variables.
    """
    def __init__(self, bucket_name="my-ohlcv-bucket", cache_size=128):
        self.bucket_name = bucket_name
        self.cache = LRUCache(maxsize=cache_size)

        endpoint_url = os.environ.get("S3_ENDPOINT_URL")
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
        existing_buckets = [b['Name'] for b in self.s3.list_buckets().get('Buckets', [])]
        if self.bucket_name not in existing_buckets:
            self.s3.create_bucket(Bucket=self.bucket_name)
            print(f"Created bucket '{self.bucket_name}' on {self.s3.meta.endpoint_url}.")

    def store_symbol(self, market_name: str, timeframe: str, symbol: str,
                     df: pd.DataFrame, append: bool = True,
                     partition_type: PartitionType = PartitionType.NONE):
        """
        Stores (or appends) a symbol’s OHLCV data as Parquet files in S3.

        If partition_type is DAILY or MONTHLY, the data is grouped by that partition
        (based on the 'timestamp' column) and each partition is stored separately.
        Otherwise, the entire DataFrame is stored in one file.
        """
        if partition_type == PartitionType.NONE:
            key = f"{market_name}/{timeframe}/{symbol}/ohlcv_data.parquet"
            if append:
                existing_df = self._download_parquet_if_exists(key)
                if existing_df is not None and not existing_df.empty:
                    df = pd.concat([existing_df, df], ignore_index=True)
                    df.drop_duplicates(subset=['timestamp'], inplace=True)
            buffer = BytesIO()
            df.to_parquet(buffer, index=False, compression='snappy')
            buffer.seek(0)
            self.s3.put_object(Bucket=self.bucket_name, Key=key, Body=buffer.read())
            print(f"Stored {len(df)} rows to s3://{self.bucket_name}/{key}")
        else:
            # Create partition key based on 'timestamp'
            if partition_type == PartitionType.DAILY:
                df['partition'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d')
            elif partition_type == PartitionType.MONTHLY:
                df['partition'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m')
            else:
                raise ValueError("Unsupported partition type. Use DAILY or MONTHLY.")

            # Store each partition separately
            for partition_value, group in df.groupby('partition'):
                key = f"{market_name}/{timeframe}/{symbol}/{partition_value}/ohlcv_data.parquet"
                if append:
                    existing_df = self._download_parquet_if_exists(key)
                    if existing_df is not None and not existing_df.empty:
                        group = pd.concat([existing_df, group], ignore_index=True)
                        group.drop_duplicates(subset=['timestamp'], inplace=True)
                buffer = BytesIO()
                group.to_parquet(buffer, index=False, compression='snappy')
                buffer.seek(0)
                self.s3.put_object(Bucket=self.bucket_name, Key=key, Body=buffer.read())
                print(f"Stored {len(group)} rows to s3://{self.bucket_name}/{key}")

    def fetch_symbol(self, market_name: str, timeframe: str, symbol: str,
                 partition_type: PartitionType = PartitionType.NONE,
                 start_date: str = '', end_date: str = '') -> pd.DataFrame:
        """
        Fetches OHLCV data for a symbol.

        If partition_type is NONE, a single file is fetched.
        If partition_type is DAILY or MONTHLY, and start_date/end_date are provided,
        it retrieves partitions in that date range.
        Otherwise, it lists all available partitions for that symbol.
        """
        if partition_type in (None, PartitionType.NONE):
            key = f"{market_name}/{timeframe}/{symbol}/ohlcv_data.parquet"
            if key in self.cache:
                return self.cache[key]
            df = self._download_parquet_if_exists(key)
            if df is not None:
                self.cache[key] = df
            return df if df is not None else pd.DataFrame()
        else:
            keys = []
            if start_date and end_date:
                start_dt = pd.to_datetime(start_date)
                end_dt = pd.to_datetime(end_date)
                if partition_type == PartitionType.DAILY:
                    date_range = pd.date_range(start_dt, end_dt, freq='D')
                    for dt in date_range:
                        partition_value = dt.strftime('%Y-%m-%d')
                        key = f"{market_name}/{timeframe}/{symbol}/{partition_value}/ohlcv_data.parquet"
                        keys.append(key)
                elif partition_type == PartitionType.MONTHLY:
                    current = start_dt.to_period('M')
                    end_period = end_dt.to_period('M')
                    while current <= end_period:
                        partition_value = current.strftime('%Y-%m')
                        key = f"{market_name}/{timeframe}/{symbol}/{partition_value}/ohlcv_data.parquet"
                        keys.append(key)
                        current = current + 1
                else:
                    raise ValueError("Unsupported partition type. Use DAILY or MONTHLY.")
            else:
                # No date range provided: list all partition keys for the symbol
                prefix = f"{market_name}/{timeframe}/{symbol}/"
                response = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
                if 'Contents' in response:
                    for obj in response['Contents']:
                        key = obj['Key']
                        if key.endswith("ohlcv_data.parquet"):
                            keys.append(key)
            
            dfs = []
            with ThreadPoolExecutor(max_workers=8) as executor:
                future_to_key = {executor.submit(self._download_parquet_if_exists, key): key for key in keys}
                for future in future_to_key:
                    key = future_to_key[future]
                    df_part = future.result()
                    if df_part is not None and not df_part.empty:
                        dfs.append(df_part)
                        self.cache[key] = df_part
            if dfs:
                combined = pd.concat(dfs, ignore_index=True)
                combined.sort_values('timestamp', inplace=True)
                return combined
            else:
                return pd.DataFrame()


    def delete_symbol(self, market_name: str, timeframe: str, symbol: str,
                      partition_type: PartitionType = PartitionType.NONE, partition_value: str = ''):
        """
        Deletes OHLCV data for a symbol.

        If partition_type is NONE, deletes the entire file.
        If partition_type is DAILY or MONTHLY and partition_value is given, deletes that specific partition.
        If partition_value is not provided, deletes all partition files under the symbol.
        Also removes the deleted keys from the cache.
        """
        if partition_type in (None, PartitionType.NONE):
            key = f"{market_name}/{timeframe}/{symbol}/ohlcv_data.parquet"
            try:
                self.s3.delete_object(Bucket=self.bucket_name, Key=key)
                if key in self.cache:
                    del self.cache[key]
                print(f"Deleted s3://{self.bucket_name}/{key}")
            except self.s3.exceptions.NoSuchKey:
                pass
        else:
            if partition_value:
                key = f"{market_name}/{timeframe}/{symbol}/{partition_value}/ohlcv_data.parquet"
                try:
                    self.s3.delete_object(Bucket=self.bucket_name, Key=key)
                    if key in self.cache:
                        del self.cache[key]
                    print(f"Deleted s3://{self.bucket_name}/{key}")
                except self.s3.exceptions.NoSuchKey:
                    pass
            else:
                # Delete all partitions for this symbol
                prefix = f"{market_name}/{timeframe}/{symbol}/"
                response = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
                if 'Contents' in response:
                    for obj in response['Contents']:
                        key = obj['Key']
                        try:
                            self.s3.delete_object(Bucket=self.bucket_name, Key=key)
                            if key in self.cache:
                                del self.cache[key]
                            print(f"Deleted s3://{self.bucket_name}/{key}")
                        except Exception as e:
                            print(f"Error deleting {key}: {e}")

    def _download_parquet_if_exists(self, key: str) -> pd.DataFrame or None:
        """
        Downloads a Parquet file from S3 if it exists.
        Returns the DataFrame or None if not found.
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
