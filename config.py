from os import getenv


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


class Config(metaclass=SingletonMeta):
    """
    Loading .env file and other configs to be able to get it in all project.
    """

    # Discord Bot Token
    TOKEN: str = getenv("TOKEN", default=None)
    SUPABASE_URL: str = getenv("SUPABASE_URL")
    SUPABASE_KEY: str = getenv("SUPABASE_KEY")
    FRONT_BASE_URL: str = getenv("FRONT_BASE_URL", "https://mngt-vercel.com")
