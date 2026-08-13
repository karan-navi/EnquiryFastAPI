from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    server_port: int = 7005
    server_address: str = "127.0.0.1"
    notificationapi__url: str = "http://localhost:7006/notificationapi/notification/v1/send-event-notification"
    database_url: str
    enquiry_reminder_threshold_hours: int = 72

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()