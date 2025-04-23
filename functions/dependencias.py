from database import FichaSessionLocal, IdentidadeSessionLocal


def get_ficha_db():
    db = FichaSessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_identidade_db():
    db = IdentidadeSessionLocal()
    try:
        yield db
    finally:
        db.close()