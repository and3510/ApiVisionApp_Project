import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

load_dotenv()


# Banco 1: SSP_Usuario
SSP_USUARIO_DATABASE_URL = os.getenv("SSP_USUARIO_DATABASE_URL")

ssp_usuario_engine = create_engine(SSP_USUARIO_DATABASE_URL)
SspUsuarioSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=ssp_usuario_engine)
SspUsuarioBase = declarative_base()


# Banco 2: SSP_CRIMINOSOS
SSP_CRIMINOSOS_DATABASE_URL = os.getenv("SSP_CRIMINOSOS_DATABASE_URL")

ssp_criminosos_engine = create_engine(SSP_CRIMINOSOS_DATABASE_URL)
SspCriminososSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=ssp_criminosos_engine)
SspCriminososBase = declarative_base()
