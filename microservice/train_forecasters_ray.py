from typing import Tuple
import logging
import os
import time

import helpers

import config_module as cfg

import kaggle

import ray
import ray.data
import pandas as pd
import numpy as np

import mlflow
import mlflow.prophet
from mlflow.client import MlflowClient

from prophet import Prophet

cfg.set(os.path.join(os.path.dirname(__file__), 'config.yaml'))

# Connect to the remote mlflow server
mlflow_handler = helpers.MlflowHandler()

def download_kaggle_dataset(kaggle_dataset: str = "pratyushakar/rossmann-store-sales") -> None:
    api = kaggle.api
    print(api.get_config_value('username'))
    kaggle.api.dataset_download_files(
        kaggle_dataset, path="./data/", unzip=True, quiet=False)

def prep_store_data(
    df: pd.DataFrame,
    store_id: int = 4,
    store_open: int = 1
) -> pd.DataFrame:
    df_store = df[
        (df['Store'] == store_id) &
        (df['Open'] == store_open)
    ].reset_index(drop=True)
    df_store['Date'] = pd.to_datetime(df_store['Date'])
    df_store.rename(columns={'Date': 'ds', 'Sales': 'y'}, inplace=True)
    return df_store.sort_values('ds', ascending=True)


def train_predict(
    df: pd.DataFrame,
    store_id: int,
    train_fraction: float,
    seasonality: dict
) -> tuple[Prophet, float, str]:

    train_index = int(train_fraction*df.shape[0])
    df_train = df.copy().iloc[0:train_index]
    df_test = df.copy().iloc[train_index:]

    model = Prophet(
        yearly_seasonality=seasonality['yearly'],
        weekly_seasonality=seasonality['weekly'],
        daily_seasonality=seasonality['daily'],
        interval_width=0.95
    )

    model.fit(df_train)
    predicted = model.predict(df_test)

    # Calculate RMSE
    se = np.square(df_test['y'] - predicted['yhat'])
    mse = np.mean(se)
    rmse = np.sqrt(mse)

    return model, rmse, str(store_id)

@ray.remote(num_returns=3)
def prep_train_predict(
    df: pd.DataFrame,
    store_id: int,
    store_open: int = 1,
    train_fraction: float = 0.8,
    seasonality: dict = {'yearly': True, 'weekly': True, 'daily': False}
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, int]:
    df = prep_store_data(df, store_id=store_id, store_open=store_open)
    return train_predict(df, store_id, train_fraction, seasonality)

if __name__ == '__main__':

    file_path = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), 'data', 'train.csv')

    if os.path.exists(file_path):
        logging.info('Dataset found, reading into pandas dataframe.')
        df = pd.read_csv(file_path, usecols=['Date', 'Store', 'Open', 'Sales'])
    else:
        logging.info('Dataset not found, downloading ...')
        helpers.download_kaggle_dataset()
        logging.info('Reading dataset into pandas dataframe.')
        df = pd.read_csv(file_path, usecols=['Date', 'Store', 'Open', 'Sales'])

    # Use a subset of stores for training and serve
    store_ids = cfg.settings['stores']

    ray.init(num_cpus=4)
    df_id = ray.put(df)

    start = time.time()
    models, metrics, ids = map(
        list,
        zip(*([prep_train_predict.remote(df_id, store_id)
            for store_id in store_ids])),
    )

    ray_results = {
        'models': ray.get(models),
        'metrics': ray.get(metrics),
        'ids': ray.get(ids),
    }

    ray_core_time = time.time() - start

    ray.shutdown()

    print(f"Models trained (Ray): {len(store_ids)}")
    print(f"Time taken (Ray): {ray_core_time/60:.2f} minutes")

    print('Done!')

    print('Logging into Mlflow remote server ...')
    mlflow_handler.log_metadata_and_artifacts(
        zip(ray_results['models'],
            ray_results['metrics'],
            ray_results['ids'])
    )
