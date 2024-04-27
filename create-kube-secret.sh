file=$1s

# Create a kubernetes secret from a file provided as an argument
kubectl create secret generic mlflow-s3-password --from-file ${file}