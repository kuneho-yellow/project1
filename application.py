'''
CS50 - Project 1
kuneho-yellow
August 16, 2018

Handle routes for the book review web application
'''

import os

from flask import Flask, session, render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["POST"])
def register():
    # Check the form inputs
    username = request.form.get("username")
    password = request.form.get("password")
    displayname = request.form.get("displayname")
    usernameError = "Please enter a username"
    passwordError = "Please enter a password"
    
    if username != "":
        # Check if username already exists
        if db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).rowcount > 0:
            usernameError = f"The username '{username}' is already taken"
        else:
            usernameError = ""
    if password != "":
        passwordError = ""
    
    # User has entered valid username and password
    if usernameError == "" and passwordError == "":
        # Handle the optional display name
        if displayname != None:
            commandStr = f"INSERT INTO users (username, password, displayname) VALUES ('{username}', '{password}', '{displayname}')"
        else:
            commandStr = f"INSERT INTO users (username, password) VALUES ('{username}', '{password}')"
        # Add the new credentials to the database
        db.execute(commandStr)
        db.commit()
        return render_template("success.html")
    
    # The user didn't enter a valid username or password
    return render_template("index.html", registerusernameerror=usernameError, registerpassworderror=passwordError, registerlastusername=username, registerlastdisplayname=displayname)

@app.route("/login", methods=["POST"])
def login():
    # Check the form inputs
    username = request.form.get("username")
    password = request.form.get("password")
    usernameError = ""
    passwordError = ""
    
    # Check if the user entered a username
    if username == "":
        usernameError = "Please enter your username"
    # Check if the username is a valid
    else:
        userData = db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).fetchone()
        if userData == None:
            usernameError = f"The username '{username}' is not registered"
        # Check if the user entered a password
        elif password == "":
            passwordError = "Please enter your password"
        # Check if the user entered the correct password
        elif password != userData.password:
            passwordError = "Incorrect password"
            
    # Log in if there's no error in the username or password:
    if usernameError == "" and passwordError == "":
        return render_template("login.html")
    
    # The user didn't enter a valid username or password
    return render_template("index.html", loginusernameerror=usernameError, loginpassworderror=passwordError, loginlastusername=username)
    
