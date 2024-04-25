import logging
from typing import List

from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel

from helpers import MlflowHandler, create_forecast_index

log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s' 
logging.basicConfig(format = log_format, level = logging.INFO)


handlers = {}
models = {}
MODEL_BASE_NAME = f'prophet-retail-forecaster-store-'

class Forecastrequest(BaseModel):
    store_id: str
    begin_date: str | None
    end_date: str | None

async def get_service_handlers():
    mlflow_handler = MlflowHandler()
    print(f'The tracking uri is: {mlflow_handler.tracking_uri}')
    global handlers
    handlers['mlflow'] = mlflow_handler
    logging.info('Retrieving mlflow handler {}'.format(mlflow_handler))
    handlers['mlflow'].start_server()
    logging.info('Started Mlflow server')

@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_service_handlers()
    logging.info('Updated global service handlers')
    yield
    handlers['mlflow'].stop_server()
    logging.info('Stopped the Mlflow server')
    handlers.clear()
    models.clear()
    logging.info('Released resources')

app = FastAPI(lifespan=lifespan)

@app.get('/health/', status_code=200)
async def healthcheck():
    global handlers
    logging.info('Got handlers in health check')
    return {
        'serviceStatus': 'OK',
        'modelTrackingHealth': handlers['mlflow'].check_mlflow_health()
    }

async def get_model(store_id: str):
    global handlers
    global models
    model_name = MODEL_BASE_NAME + store_id
    if model_name not in models:
        models[model_name] = handlers['mlflow'].get_production_model(store_id=store_id)
    return models[model_name]

@app.post('/forecast/', status_code=200)
async def return_foreast(forecast_request: List[Forecastrequest]):
    forecasts = []
    for item in forecast_request:
        forecast_result = {}
        forecast_result['request'] = item.dict()
        model = await get_model(item.store_id)
        if model is None:
            forecast_result['forecast'] = \
                'Forecase is not possible for this store id at the moment'
        else:
            forecast_input = create_forecast_index(
                begin_date=item.begin_date,
                end_date=item.end_date
            )
            model_prediction = model.predict(forecast_input)[['ds', 'yhat']]\
            .rename(columns={'ds': 'timestamp', 'yhat': 'value'})
            model_prediction['value'] = model_prediction['value'].astype(int)
            forecast_result['forecast'] = model_prediction.to_dict('records')
        forecasts.append(forecast_result)
    return forecasts


if __name__ == '__main__':
    
    import subprocess
    import uvicorn
    import time
    import os
    
    time.sleep(4)

    # Start the web application
    uvicorn.run(app, host='0.0.0.0', port=8000)
