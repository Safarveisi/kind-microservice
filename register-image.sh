image=$1
tag=$2

docker build -t ciaa/${image}:${tag} .
docker push ciaa/${image}:${tag}