# A forecast service based on Prophet
A web applciation (powered by fast api) that receives prediction requests for five 
different store ids. 

## Training
Train 5 different Prophet models using a kaggle dataset (`microservice/train_forecasters_ray.py`). To get the dataset, we will use the kaggle python package. 

## Experiment tracking and model registery
Use a remote Mlflow server for experiment tracking purposes and as a model registery.  

## Serve
Download the registered Prophet models (for each store id) from the Mlflow artifactory location 
and make predictions for the requested store id and the time range. The web application can run on a kind kubernetes
cluster (`kube-deploy.yaml`) or in a standalone docker container (`docker-compose.yaml`). In the former case, an ingress load balancer is used to communicate with the inference service from outside of the kind cluster. 

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