from typing import Tuple
import logging
import os
import time

import helpers

import config_module as cfg

import ray
import ray.data
import pandas as pd
import numpy as np

import mlflow
import mlflow.prophet
from mlflow.client import MlflowClient

from prophet import Prophet

cfg.set(os.path.join(os.path.dirname(__file__), 'config.yaml'))


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
) -> tuple[Prophet, float, int]:

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

    return model, rmse, store_id


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


def log_to_mlflow(
    ray_results: dict,
    tracking_uri: str = 'http://0.0.0.0:5001'
) -> None:

    helpers.log_stores_artifacts_and_metadata(
        zip(ray_results['model'], ray_results['rmse'],
            ray_results['store_id']),
        cfg.settings['threshold']['rmse']
    )


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

    store_ids = df['Store'].unique()

    ray.init(num_cpus=4)
    df_id = ray.put(df)

    start = time.time()
    model_obj_refs, rmse_obj_refs, store_id_obj_refs = map(
        list,
        zip(*([prep_train_predict.remote(df_id, store_id)
            for store_id in store_ids])),
    )

    ray_results = {
        'model': ray.get(model_obj_refs),
        'rmse': ray.get(rmse_obj_refs),
        'store_id': ray.get(store_id_obj_refs),
    }

    ray_core_time = time.time() - start

    ray.shutdown()

    print(f"Models trained (Ray): {len(store_ids)}")
    print(f"Time taken (Ray): {ray_core_time/60:.2f} minutes")

    print('Done!')

    print('Logging into Mlflow local server ...')
    log_to_mlflow(ray_results)
