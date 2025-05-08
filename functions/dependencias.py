from config.database import SspUsuarioSessionLocal, SspCriminososSessionLocal


def get_ssp_usuario_db():
    db = SspUsuarioSessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_ssp_criminosos_db():
    db = SspCriminososSessionLocal()
    try:
        yield db
    finally:
        db.close()

