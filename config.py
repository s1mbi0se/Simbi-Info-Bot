from os import getenv

from dotenv import load_dotenv


class SingletonMeta(type):
    """
    Singleton class for instantiate only one time the configs.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


def _verify_credentials(credentials: dict):
    return True if "" in credentials.values() else False


class Config(metaclass=SingletonMeta):
    """
    Loading .env file and other configs to be able to get it in all project.
    """

    load_dotenv()
    # URL for the revaluation sheet
    URL_SHEET = getenv("URL_SHEET", default="")

    # Discord Bot Token
    TOKEN = getenv("TOKEN", default=None)

    # Cargos and channel to be notified (revaluation)
    CARGOS = getenv("CARGOS_LIST", default="").split(",")
    INFO_CHANNEL = getenv("INFO_CHANNEL", default="")

    # Time to check the revaluation
    HOUR = int(getenv("HOUR", default=8))
    MINUTE = int(getenv("MINUTE", default=30))

    # Days in advance to check the revaluation
    DAYS_IN_ADVANCE = int(getenv("DAYS_IN_ADVANCE", default=15))

    # Google Service Account Access Credentials
    CREDENTIALS: dict = {
        "type": getenv("TYPE", default=""),
        "project_id": getenv("PROJECT_ID", default=""),
        "private_key_id": getenv("PRIVATE_KEY_ID", default=""),
        "private_key": getenv("PRIVATE_KEY", default=""),
        "client_email": getenv("CLIENT_EMAIL", default=""),
        "client_id": getenv("CLIENT_ID", default=""),
        "auth_uri": getenv("AUTH_URI", default=""),
        "token_uri": getenv("TOKEN_URI", default=""),
        "auth_provider_x509_cert_url": getenv(
            "AUTH_PROVIDER_x509_CERT_URL", default=""
        ),
        "client_x509_cert_url": getenv("CLIENT_x509_CERT_URL", default=""),
        "universe_domain": getenv("UNIVERSE_DOMAIN", default=""),
    }

    IS_EMPTY = _verify_credentials(CREDENTIALS)
