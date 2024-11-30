import os
import shutil

import uvicorn
from dotenv import load_dotenv

from api import app

if not os.path.isfile(".env") and os.path.isfile(".env.example"):
    """
    копирует переменные среды если их нет
    """
    shutil.copyfile(
        src=".env.example",
        dst=".env"
    )

if os.path.isfile(".env"):
    load_dotenv(".env")

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8056)