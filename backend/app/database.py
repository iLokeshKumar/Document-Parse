from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Fallback to SQLite if no DB URL provided (for safety/testing)
    DATABASE_URL = "sqlite:///./users.db"
    print("WARNING: DATABASE_URL not found, using SQLite fallback.")


def get_engine(url):
    try:
        engine = create_engine(url)
        # Test connection
        with engine.connect() as connection:
            pass
        return engine
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None

engine = None
if DATABASE_URL:
    print(f"Attempting to connect to: {DATABASE_URL}")
    engine = get_engine(DATABASE_URL)

if not engine:
    print("WARNING: Falling back to SQLite.")
    DATABASE_URL = "sqlite:///./users.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="lawyer") # admin, lawyer, paralegal
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    mfa_secret = Column(String, nullable=True)
    mfa_enabled = Column(Boolean, default=False)
    mfa_disable_otp = Column(String, nullable=True)
    mfa_disable_otp_expiry = Column(String, nullable=True)
    phone_number = Column(String, unique=True, nullable=True, index=True)

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    query = Column(String)
    response = Column(String)
    rating = Column(String)  # "thumbs_up" or "thumbs_down"
    categories = Column(String, nullable=True)  # JSON string of selected categories
    comment = Column(String, nullable=True)
    timestamp = Column(String)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize database: {e}")
