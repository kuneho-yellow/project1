'''
CS50 - Project 1
kuneho-yellow
August 16, 2018

Import books.csv file into the database
'''

import os
import csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# Create a table for the books.csv contents
db.execute("CREATE TABLE books (isbn VARCHAR PRIMARY KEY NOT NULL, title VARCHAR, author VARCHAR, year INTEGER);")

# Open and read books.csv
with open('books.csv', newline='') as csvfile:
    headers = []
    for line in csv.reader(csvfile, delimiter=',', quotechar='"'):
        # Skip the headers
        if len(headers) == 0:
            for header in line:
                headers.append(header)
            continue
        # Load the values into the database
        isbn = line[0]
        # Double up any single quotes in the title and author
        title = ("''").join(line[1].split("'"))
        author = ("''").join(line[2].split("'"))
        year = int(line[3])
        insertCommand = f"INSERT INTO books (isbn, title, author, year) VALUES ('{isbn}', '{title}', '{author}', {year})"
        db.execute(insertCommand)
        
# Save changes to the database
db.commit()