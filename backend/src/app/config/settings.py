from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Wallets"
    environment: str = "development"
    database_url: str = "postgresql://postgres@localhost:5432/wallets"
    migration_database_url: str = "postgresql://postgres@localhost:5432/wallets"

    jwt_secret: str
    hmac_secret: str
    jwt_expire_minutes: int = 60
    apple_private_key_password: str
    apple_private_key_path: str = "/home/djordje/.wallets-secrets/apple-pass.key.enc"
    google_service_account_path: str = "/home/djordje/.wallets-secrets/google/google-wallet-service-account.json"
    google_wallet_issuer_id: str
    apple_web_service_url: str | None = None
    apple_pass_type_identifier: str = "pass.com.edulibris.wallet.demo01"

    smtp_host: str | None = None
    smtp_port: int = 465
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_ssl: bool = True
    email_from: str = "noreply@edulibris.com"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

