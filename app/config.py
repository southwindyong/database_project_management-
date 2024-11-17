import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql://admin:data@localhost:5432/project")
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
