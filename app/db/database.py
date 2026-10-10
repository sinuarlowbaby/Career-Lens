from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./career_lens.db")

# Fix for cloud databases (AWS RDS, Heroku, Render) providing postgres:// prefix
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    # AWS RDS / PostgreSQL production pool settings
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Proactively verify connection liveness before executing queries
        pool_recycle=300,    # Recycle connections every 5 minutes to prevent AWS NAT/firewall drops
        pool_size=10,        # Number of connections kept open in pool
        max_overflow=20      # Extra connections allowed during peak bursts
    )

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()