from os import getenv
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')

load_dotenv(dotenv_path)

API_KEY = str(getenv("API_KEY"))
SECRET_KEY = str(getenv("SECRET_KEY"))
TF_DURATION=str(getenv("TF_DURATION"))
TF_UNIT=str(getenv("TF_UNIT"))
CANDLE_LIMIT=int(getenv("CANDLE_LIMIT"))
LEVERAGE=int(getenv("LEVERAGE"))
RISK_OF_RUIN=int(getenv("RISK_OF_RUIN"))
SL_PERCENTAGE=int(getenv("SL_PERCENTAGE"))
TP_PERCENTAGE=int(getenv("TP_PERCENTAGE"))
