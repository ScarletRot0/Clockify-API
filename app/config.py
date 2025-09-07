import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_TOKEN = os.getenv("SECRET_TOKEN")
    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True") == "True"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")
    MAIL_RECIPIENT = os.getenv("MAIL_RECIPIENT")
    MAIL_ADDITIONAL_RECIPIENTS = os.getenv("MAIL_ADDITIONAL_RECIPIENTS", "")
    CLOCKIFY_SECRET_TOKEN_START = os.getenv("CLOCKIFY_SECRET_TOKEN_START")
    CLOCKIFY_SECRET_TOKEN_END = os.getenv("CLOCKIFY_SECRET_TOKEN_END")
    CLOCKIFY_SECRET_TOKEN_EDIT = os.getenv("CLOCKIFY_SECRET_TOKEN_EDIT")
    CLOCKIFY_SECRET_TOKEN_DELETE = os.getenv("CLOCKIFY_SECRET_TOKEN_DELETE")
    CLOCKIFY_SECRET_TOKEN_MANUAL_CREATE = os.getenv("CLOCKIFY_SECRET_TOKEN_MANUAL_CREATE")
    EMAIL_MAX_RETRIES = os.getenv("EMAIL_MAX_RETRIES")
    EMAIL_RETRY_DELAY = os.getenv("EMAIL_RETRY_DELAY")
    EMAIL_PROCESS_INTERVAL = os.getenv("EMAIL_PROCESS_INTERVAL")

