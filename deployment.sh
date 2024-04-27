type=$1

envsubst < kube-deploy.yaml | kubectl ${type} -f -