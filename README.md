# A forecast service based on Prophet
A web applciation (powered by fast api) that receives prediction requests for five 
different store ids. The application runs within a kind kubernetes cluster with two
pad replicas and a load balancer.  

## Training
Train 5 different Prophet models using a kaggle dataset. To get the dataset, use the kaggle
python package. 

## Experiment tracking and model registery
Use a remote Mlflow server for experiment tracking purposes and as a model registery.  

## Serve
Download the registered Prophet models (for each store id) from the Mlflow artifactory location 
and make predictions for the requested store id and the time range. The inference system runs on a kind kubernetes
cluster to make the application scalable. An Ingress service is used as for the load balancer and a way to communicate with the inference service from outside of the cluster. The application code resides in a docker image (see `Dockerfile`) deployed into the Kubernetes cluster (see `kube-deploy.yaml`). 

## System
![ezcv logo](https://github.com/Safarveisi/microservice/blob/master/comps.png)

## Usage
|File/Dir|Desc|
|---|---|
|commit-dir|Files created by targets in the Makefile are pushed here|
