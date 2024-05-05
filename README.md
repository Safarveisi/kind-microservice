# Service
A web applciation (powered by fast api) that receives forecasting requests for different time ranges and for five 
different store ids. The request body (post) and its response follow the following schema

Request (post):

```json
[
    {
        "store_id": "1",
        "begin_date": "2023-01-02",
        "end_date": "2023-01-07"
    },
    {
        "store_id": "2",
        "begin_date": "2023-01-02",
        "end_date": "2023-01-07"
    }
]
```

Response:

```json
[
    {
        "request": {
            "store_id": "1",
            "begin_date": "2023-01-02",
            "end_date": "2023-01-07"
        },
        "forecast": [
            {
                "timestamp": "2023-01-02T00:00:00",
                "value": 7107
            },
            {
                "timestamp": "2023-01-03T00:00:00",
                "value": 6453
            },
            {
                "timestamp": "2023-01-04T00:00:00",
                "value": 6199
            },
            {
                "timestamp": "2023-01-05T00:00:00",
                "value": 5976
            },
            {
                "timestamp": "2023-01-06T00:00:00",
                "value": 6164
            },
            {
                "timestamp": "2023-01-07T00:00:00",
                "value": 6230
            }
        ]
    },
    {
        "request": {
            "store_id": "2",
            "begin_date": "2023-01-02",
            "end_date": "2023-01-07"
        },
        "forecast": [
            {
                "timestamp": "2023-01-02T00:00:00",
                "value": 7069
            },
            {
                "timestamp": "2023-01-03T00:00:00",
                "value": 6205
            },
            {
                "timestamp": "2023-01-04T00:00:00",
                "value": 6653
            },
            {
                "timestamp": "2023-01-05T00:00:00",
                "value": 5757
            },
            {
                "timestamp": "2023-01-06T00:00:00",
                "value": 5385
            },
            {
                "timestamp": "2023-01-07T00:00:00",
                "value": 3446
            }
        ]
    }
]
```  

## Training
Train 5 different Prophet models using a kaggle dataset (`microservice/train_forecasters_ray.py`). To get the dataset, we will use the kaggle python package. 

## Experiment tracking and model registery
Use a remote Mlflow server for experiment tracking purposes and as a model registery.  

## Serve
Download the registered Prophet models (for each store id) from the Mlflow artifactory location 
and make predictions for the requested store id and the time range. The web application can run on a kind kubernetes
cluster (`kube-deploy.yaml`) or in a standalone docker container (`docker-compose.yaml`). In the former case, an ingress load balancer is used to communicate with the inference service from outside of the cluster. 

To initialize the web application in the container, a few environment variables will be injected (through a configmap while deploying in a kind cluster or secrets otherwise) into the container before starting the service.   

## System
![ezcv logo](https://github.com/Safarveisi/microservice/blob/master/comps.png)

## Usage
| **File/Dir** | **Desc** |
| --- | --- |
| `commit-dir` | Files created by targets in the Makefile are pushed here |
| `microservice` | Source code for the app |
| `Dockerfile` | Instructions to create the docker image of the app |
| `Makefile` | Environment management and automation of the workflows |
| `docker-compose.yaml` | Container orchestration |
| `kind-cluster-configurations.yaml` | Configurations for the kind k8s cluster |
| `kube-deploy.yaml` | Manifest to deploy the app in the kind cluster |