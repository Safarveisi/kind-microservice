KUBE_DEPLOYMENT_FILE ?= kube-deploy.yaml
KUBE_CONFIG_PATH ?= $(HOME)/.kube/config

.DEFAULT_GOAL := help

help:

	@echo "Available targets: "
	@echo "	help	Display this help message"
	@echo "	kube-config	Path to the kubernetes config file"
	@echo "	build-image	Build the latest Docker image"
	@echo "	deployed	Deploy the service (manifest: $(KUBE_DEPLOYMENT_FILE))"
	@echo "	clean-kube	Remove the deployment (manifest: $(KUBE_DEPLOYMENT_FILE))"

kube-config:
	@echo "Kubeconfig path: $(KUBE_CONFIG_PATH)"

build-image:
	@docker build -t ciaa/forecast-service:latest .; \
	docker push ciaa/forecast-service:latest; \
	touch $@

deployed:
	@envsubst < $(KUBE_DEPLOYMENT_FILE) | kubectl apply -f -; \
	touch $@

clean-kube: 
	@envsubst < $(KUBE_DEPLOYMENT_FILE) | kubectl delete -f -; \
	touch $@

clean:
	@rm -f deployed clean-kube build-image

.PHONY: kube-config clean help