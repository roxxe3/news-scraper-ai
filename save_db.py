from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv
from helpers import logger

# Load environment variables
load_dotenv()

# Get database URL from environment variable with fallback
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://username:password@localhost/mydatabase"
)

# Define a base class using SQLAlchemy
Base = declarative_base()

# Define your Article class (mapped to the "articles" table)
class Article(Base):
    __tablename__ = 'articles'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    link = Column(String(255), nullable=False)
    category = Column(String(100))
    topic = Column(String(100))
    published_date = Column(DateTime)
    updated_date = Column(DateTime)
    content = Column(Text)
    
    def __repr__(self):
        return f"<Article(title='{self.title[:30]}...', category='{self.category}', topic='{self.topic}')>"

# Create an engine and session factory
try:
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")
    raise

def init_db():
    """Initialize database connection and create tables if they don't exist"""
    try:
        Base.metadata.create_all(engine)
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")
        return False