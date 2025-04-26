from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Define your database URL (adjust the username, password, host, and database name)
DATABASE_URL = "postgresql://username:password@localhost/mydatabase"

# Create an engine to connect to the database
engine = create_engine(DATABASE_URL)

# Define a base class using SQLAlchemy
Base = declarative_base()

# Define your Article class (mapped to the "articles" table)
class Article(Base):
    __tablename__ = 'articles'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    link = Column(String(255), nullable=False)
    category = Column(String(100))
    published_date = Column(DateTime)
    updated_date = Column(DateTime)
    content = Column(Text)

# Create a session to interact with the database
Session = sessionmaker(bind=engine)
session = Session()

# Query all rows from the articles table
articles = session.query(Article).all()

# Print the articles
for article in articles:
    print(f"ID: {article.id}, Title: {article.title}, Link: {article.link}, Category: {article.category}")

# Close the session
session.close()
