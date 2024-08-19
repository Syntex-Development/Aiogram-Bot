from dataclasses import dataclass
from environs import Env


@dataclass
class Config:
    TOKEN : str
    ADMIN : int
    DATABASE_URL : str
    

def load_config(path) -> Config:
    env = Env()
    env.read_env(path)
    
    return Config(
        env.str("TOKEN"),
        env.int("ADMIN"),
        env.str("DATABASE_URL"),
    )
    
config = load_config('.env')