KUBE_DEPLOYMENT_FILE := kube-deploy.yaml
KUBE_CONFIG_PATH := $(HOME)/.kube/config
COMMIT_DIR := commit-dir

.DEFAULT_GOAL := help

help:
	@echo "Available targets: "
	@echo "	help	Display this help message"
	@echo "	kube-config	Path to the kubernetes config file"
	@echo "	$(COMMIT_DIR)/build-image	Build the latest Docker image"
	@echo "	$(COMMIT_DIR)/deploy	Deploy the service (manifest: $(KUBE_DEPLOYMENT_FILE))"
	@echo "	$(COMMIT_DIR)/remove-deploy	Remove the deployment (manifest: $(KUBE_DEPLOYMENT_FILE))"
	@echo "	$(COMMIT_DIR)	Create $(COMMIT_DIR) directory to which commit files are pushed"
	@echo "	clean-kube-commit	Remove all kubernetes commit files from $(COMMIT_DIR)"
	@echo "	clean-docker-commit	Remove all docker commit files from $(COMMIT_DIR)"

kube-config:
	@echo "Kubeconfig path: $(KUBE_CONFIG_PATH)"

$(COMMIT_DIR)/build-image: $(COMMIT_DIR)
	@read -p "Enter the version for the image: " version; \
	docker build -t ciaa/forecast-service:$$version .; \
	docker push ciaa/forecast-service:$$version; \
	touch $@

$(COMMIT_DIR)/deploy: $(COMMIT_DIR)
	@read -p "Enter the image version: " version; \
	VERSION=$$version envsubst < $(KUBE_DEPLOYMENT_FILE) | kubectl apply -f -; \
	touch $@

$(COMMIT_DIR)/remove-deploy: $(COMMIT_DIR)
	@kubectl delete -f $(KUBE_DEPLOYMENT_FILE); \
	touch $@

clean-docker-commit: $(COMMIT_DIR)
	@rm -f $</build-image

clean-kube-commit: $(COMMIT_DIR)
	@rm -f $</deploy $</remove-deploy

$(COMMIT_DIR): 
	@if [ ! -d "$@" ]; then \
		mkdir -p "$@"; \
		echo "Directory created: $@"; \
	else \
		echo "Directory already exists: $@"; \
	fi

setup-env:
	@VENV=$$(poetry env info -p); \
	rm -rf $$VENV; \
	pyenv install --skip-existing; \
	PYTHON_VERSION=$$(pyenv version-name); \
	echo "Required python version is $$PYTHON_VERSION"; \
	echo "Setting the env to $(HOME)/.pyenv/versions/$$PYTHON_VERSION/bin/python"; \
	poetry env use $(HOME)/.pyenv/versions/$$PYTHON_VERSION/bin/python; \
	poetry config --local virtualenvs.in-project true; \
	poetry install

update-env:
	@read -p "Enter the package to add: " package; \
	poetry add $$package

.PHONY: update-env setup-env kube-config clean help clean-docker-commit clean-kube-commit