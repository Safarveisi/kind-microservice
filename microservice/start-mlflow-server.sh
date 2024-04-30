mlflow server \
    --backend-store-uri sqlite:///mlflow.db \
    --default-artifact-root s3://customerintelligence/advanced-analytics/microservice/ \
    --host 0.0.0.0 \
    --port 5001