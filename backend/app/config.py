from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    keycloak_url: str
    keycloak_realm: str
    keycloak_client_id: str
    keycloak_client_secret: str
    keycloak_admin_user: str
    keycloak_admin_password: str
    jwt_algorithm: str = "RS256"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
