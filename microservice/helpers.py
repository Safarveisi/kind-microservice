import os
import logging
import datetime
from typing import Iterator, Tuple

import pandas as pd
from prophet import Prophet

import mlflow
from mlflow.tracking import MlflowClient

import config_module as cfg

log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(format=log_format, level=logging.INFO)

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

        self.tracking_uri: str = os.getenv('MLFLOW_TRACKING_URI')
        mlflow.set_tracking_uri(self.tracking_uri)
        self.client: MlflowClient = MlflowClient()

    def check_mlflow_health(self) -> None:
        try:
            experiments = self.client.search_experiments()
            return 'Service returning experiments'
        except:
            return 'Error calling mlflow'

    def get_model_in_production(self, model_name: str) -> Prophet | None:
        try:
            return mlflow.prophet.load_model(
                model_uri=f'models:/{model_name}/production'
            )
        except mlflow.exceptions.RestException:
            return None

    def set_model_version_to_production(self, model_name: str) -> None:
        '''Sets the stage of the latest version of a registered model to production'''
        latest_version = self.get_model_latest_version(model_name)
        self.client.transition_model_version_stage(
            name=model_name, version=latest_version, stage='production')

    def get_latest_production_version(self, model_name: str) -> str | None:
        '''Get the latest version of the registered model in production'''
        version = None
        model_versions = self.client.search_model_versions(f"name='{model_name}'")
        for mv in model_versions:
            if mv.current_stage == 'Production':
                version = mv.version
        return version

    def get_model_latest_version(self, model_name: str) -> str:
        '''Get the latest version of a registered model'''
        latest_version = sorted(self.client.search_model_versions(f"name='{model_name}'"),
                                key=lambda x: x.creation_timestamp)[-1]
        return latest_version.version

    def create_experiment(self, experiment_name: str) -> str:
        if mlflow.get_experiment_by_name(experiment_name) is None: 
            mlflow.create_experiment(experiment_name)
        return mlflow.get_experiment_by_name(experiment_name).experiment_id

    def log_metadata_and_artifacts(
        self, load: Iterator[Tuple[Prophet, float, str]],
    ) -> None:
        # Extract the artifact and metadata from the tuple object
        for metadata_and_artifact in load:
            model, rmse, store_id = metadata_and_artifact
            model_name = f'prophet-forecaster-store-{store_id}'
            experiment_id = self.create_experiment(f'forecast-service/store-{store_id}')
            with mlflow.start_run(experiment_id=experiment_id) as run:
                mlflow.prophet.log_model(
                    model, artifact_path='estimator', registered_model_name=model_name)
                # Log the metric (rmse)
                mlflow.log_metrics({'rmse': rmse})

            if rmse <= cfg.settings['threshold']['rmse']:
                if (previous_prod_version := self.get_latest_production_version(
                    model_name=model_name)) is None:
                    logging.info(
                        'None of the versions are in the production stage ' \
                        f'for {model_name}'
                    )
                else:
                    logging.info(
                        'Archiving the latest version in the production stage ' \
                        f'for {model_name}'
                    )
                    self.client.transition_model_version_stage(
                        name=model_name,
                        version=previous_prod_version,
                        stage='archived'
                    )
                    logging.info(
                        f'Version {previous_prod_version} was archived ' \
                        f'for {model_name}'    
                    )
                logging.info(
                    'Setting the latest version stage to production ' \
                    f'for {model_name}'
                )
                self.set_model_version_to_production(model_name=model_name)