# A forecast service based on Prophet
A web applciation (powered by fast api) that receives prediction requests for different 
store ids (total of 1115). The application runs within a kind kubernetes cluster with two
pad replicas and a load balancer.  

## Training
Train 1115 different Prophet models using a kaggle dataset. To get the dataset, use the kaggle
python package. 

## Experiment tracking and model registery
Use a local Mlflow server for experiment tracking purposes and as a model registery. A s3 back-end is 
used as for the artifactory location. The metadata of each experiment is saved in a local 
Sqlit db.  

## Serve
Download the registered Prophet models (for each store id) on Mlflow and make predictions
for the requested store id and the time range. The inference system runs on a kind kubernetes
cluster to make the application scalable through a load balancer (ingress). 

## Train and inference system