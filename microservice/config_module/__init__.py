import yaml

settings = None

def set(path_to_yaml: str) -> None:

    global settings

    if isinstance(path_to_yaml, str):
        # Get the config for the app
        with open(path_to_yaml, 'r') as f:
            settings = yaml.safe_load(f)
    else:
        raise ValueError('`path_to_yaml` must be a string')
