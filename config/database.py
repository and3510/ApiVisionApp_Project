import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

load_dotenv()


# Banco 1: SSP
SSP_DATABASE_URL = os.getenv("SSP_DATABASE_URL")

ssp_engine = create_engine(SSP_DATABASE_URL)
SspSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=ssp_engine)
SspBase = declarative_base()


# Banco 2: CIN
CIN_DATABASE_URL = os.getenv("CIN_DATABASE_URL")

cin_engine = create_engine(CIN_DATABASE_URL)
CinSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cin_engine)
CinBase = declarative_base()
