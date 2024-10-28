import configparser
from settings import ROOT_DIR
import os

config = configparser.ConfigParser()
PATH_CONFIG = os.path.join(ROOT_DIR, 'config.ini')
config.read(PATH_CONFIG)

# Extract API keys
openai_engine_name = config['OPENAI']['engine_name']
openai_api_key = config['OPENAI']['api_key']
openai_api_type = config['OPENAI']['api_type']
openai_api_base = config['OPENAI']['api_base']
openai_api_version = config['OPENAI']['api_version']

neptune_api_token = config['NEPTUNE']['api_token']

model_type = None
repo_url = None