'''
CS50 - Project 1
kuneho-yellow
August 18, 2018

Create additional tables in the database
'''

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# Create a table for users
db.execute("CREATE TABLE users (username VARCHAR PRIMARY KEY NOT NULL, password VARCHAR NOT NULL, displayname VARCHAR);")

# Create a table for book reviews
db.execute("CREATE TABLE reviews (key SERIAL PRIMARY KEY, isbn VARCHAR NOT NULL, username VARCHAR NOT NULL, rating INTEGER NOT NULL, review VARCHAR);")

# Save changes to the database
db.commit()