import os
import datetime
from typing import Iterator, Tuple
import subprocess
import signal

import yaml

import pandas as pd
from prophet import Prophet

import mlflow
from mlflow.tracking import MlflowClient

import config_module as cfg

# Read the config file for the web application
cfg.set(os.path.join(os.path.dirname(__file__), 'config.yaml'))

def create_forecast_index(begin_date: str = None, end_date: str = None) -> pd.DataFrame:
    
    if begin_date is None:
        begin_date = datetime.datetime.now().replace(tzinfo=None)
    else:
        begin_date = datetime.datetime.strptime(begin_date,
                     '%Y-%m-%d').replace(tzinfo=None)
    
    if end_date is None:
        end_date = begin_date + datetime.timedelta(days=7)
    else:
        end_date = datetime.datetime.strptime(end_date, 
                   '%Y-%m-%d').replace(tzinfo=None)

    forecast_index = pd.date_range(start=begin_date, end=end_date, freq='D') 
    
    return pd.DataFrame({'ds': forecast_index})

class MlflowHandler:
    
    def __init__(self) -> None:
        self.tracking_uri =  os.getenv('MLFLOW_TRACKING_URI')
        mlflow.set_tracking_uri(self.tracking_uri)
        self.client = MlflowClient()

    def start_server(self) -> None: 
        # Start the mlflow server in the background
        command = [
            "mlflow", "server",
            "--backend-store-uri", 
                cfg.settings['mlflow']['backend_store'],
            "--default-artifact-root",
                 cfg.settings['mlflow']['artifactory_location'],
            "--host",
                 "0.0.0.0",
            "--port",
                 "5001"
        ]

        self.process = subprocess.Popen(command, 
                                        stdout=subprocess.PIPE,
                                        preexec_fn=os.setsid)
    def stop_server(self) -> None:
        pid = os.getpgid(self.process.pid)
        os.killpg(pid, signal.SIGINT)

    def check_mlflow_health(self) -> None:
        try:
            experiments = self.client.search_experiments()
            return 'Service returning experiments'
        except:
            return 'Error calling mlflow'
            
    def get_production_model(self, store_id: str) -> Prophet | None:
        model_name = f'prophet-retail-forecaster-store-{store_id}'
        try:
            return mlflow.prophet.load_model(
            model_uri=f'models:/{model_name}@champion'
            )
        except mlflow.exceptions.RestException:
            return None

def download_kaggle_dataset(kaggle_dataset: str ="pratyushakar/rossmann-store-sales") -> None:
    api = kaggle.api
    print(api.get_config_value('username'))
    kaggle.api.dataset_download_files(kaggle_dataset, path="./data/", unzip=True, quiet=False)

def check_experiment_exists(name: str, tracking_uri: str = 'http://0.0.0.0:5001') -> bool:
    mlflow.set_tracking_uri(tracking_uri)
    return mlflow.get_experiment_by_name(name) is not None

def model_latest_version_metric(
    model_name: str,
    key: str = 'rmse',
    tracking_uri: str = 'http://0.0.0.0:5001',
    ) -> float:
    
    mlflow.set_tracking_uri(tracking_uri)
    client = MlflowClient()
    
    # Get the latest version of the model_name
    run_id = client.get_registered_model(name=model_name) \
        .latest_versions[0].run_id
    
    # Retrieve the metric (key) for the associated run id
    return dict(client.get_metric_history(run_id=run_id, key=key)[0])['value']

def set_model_for_service(
    model_name: str,
    tracking_uri: str = 'http://0.0.0.0:5001',
    ) -> None:
    
    '''
    Sets a model version alias to 'champion' if
    the rmse (metric) is below a threshold. This
    version will be used in serving stage. The 
    alias will be reassingned to another version
    of the model if the condition is satisfied
    after another training. 
    '''
    
    mlflow.set_tracking_uri(tracking_uri)
    client = MlflowClient()
    
    # Get the latest version of the model_name
    latest_version = client.get_registered_model(name=model_name) \
        .latest_versions[0].version
    
    client.set_registered_model_alias(
        model_name, 'champion', latest_version
    )

def log_stores_artifacts_and_metadata(
    artifacts_and_metadata: Iterator[Tuple[Prophet, float, int]],
    threshold: float,
    tracking_uri: str = 'http://0.0.0.0:5001',
) -> None:
    
    mlflow.set_tracking_uri(tracking_uri)
    client = MlflowClient()

    for to_log_tuple in artifacts_and_metadata:

        model, rmse, store_id = to_log_tuple        
        # Check if the experiment to log in already exists
        if check_experiment_exists(f'store-{store_id}'):
            print(f'Experiment store-{store_id} exists!')
        else:
            mlflow.create_experiment(f'store-{store_id}', artifact_location=S3_PATH+str(store_id))
        
        # Get the experiment id of the experiment
        experiment_id = client.get_experiment_by_name(f'store-{store_id}').experiment_id
        
        # Name of the fitted model to register
        model_name = f'prophet-retail-forecaster-store-{store_id}'

        with mlflow.start_run(experiment_id=experiment_id) as run:
            # Log the prophet model into the mlflow artifactory
            mlflow.prophet.log_model(model, artifact_path='estimator', registered_model_name=model_name)
            # Log the metric
            mlflow.log_metrics({'rmse': rmse})
            # Reassing the 'champion' alias to the new version of the model (if applicable)           
            set_model_for_service(model_name=model_name) if (rmse <= threshold) else \
                print(f'New version of {model_name} did not meet the criterion!')
