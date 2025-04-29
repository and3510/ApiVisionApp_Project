from config.database import SspSessionLocal, CinSessionLocal


def get_ssp_db():
    db = SspSessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_cin_db():
    db = CinSessionLocal()
    try:
        yield db
    finally:
        db.close()

