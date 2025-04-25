import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

load_dotenv()


# Banco 1: Ficha Criminal
FICHA_DATABASE_URL = os.getenv("FICHA_DATABASE_URL")

ficha_engine = create_engine(FICHA_DATABASE_URL)
FichaSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=ficha_engine)
FichaBase = declarative_base()


# Banco 2: Identidade
IDENTIDADE_DATABASE_URL = os.getenv("IDENTIDADE_DATABASE_URL")

identidade_engine = create_engine(IDENTIDADE_DATABASE_URL)
IdentidadeSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=identidade_engine)
IdentidadeBase = declarative_base()
