from os import getenv
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')

load_dotenv(dotenv_path)

API_KEY = str(getenv("API_KEY"))
SECRET_KEY = str(getenv("SECRET_KEY"))
API_READING_KEY = str(getenv("API_READING_KEY"))
SECRET_READING_KEY = str(getenv("SECRET_READING_KEY"))
TF_DURATION=str(getenv("TF_DURATION"))
TF_UNIT=str(getenv("TF_UNIT"))
CANDLE_LIMIT=int(getenv("CANDLE_LIMIT"))
BACK_TEST_LIMIT=int(getenv("BACK_TEST_LIMIT"))
LEVERAGE=int(getenv("LEVERAGE"))
SL_PERCENTAGE=int(getenv("SL_PERCENTAGE"))
TP_PERCENTAGE=int(getenv("TP_PERCENTAGE"))
FUTURE_POSITION_SIZE=int(getenv("FUTURE_POSITION_SIZE"))
REBALANCING_COIN=str(getenv("REBALANCING_COIN"))
REBALANCING_FAIT_COIN=str(getenv("REBALANCING_FAIT_COIN"))
REBALANCING_PERCENTAGE=int(getenv("REBALANCING_PERCENTAGE"))
LINE_NOTIFY_TOKEN=str(getenv("LINE_NOTIFY_TOKEN"))
FIXIE_URL=str(getenv("FIXIE_URL"))
DATABASE_URL=str(getenv("DATABASE_URL"))
