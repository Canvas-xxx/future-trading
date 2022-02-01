from os import getenv
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')

load_dotenv(dotenv_path)

API_KEY = str(getenv("API_KEY"))
SECRET_KEY = str(getenv("SECRET_KEY"))
