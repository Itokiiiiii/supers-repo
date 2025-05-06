from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ✅ Nueva base de datos superhero
DATABASE_URL = "mysql+pymysql://root:rootpassword@mysql:3306/superhero"


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
	
