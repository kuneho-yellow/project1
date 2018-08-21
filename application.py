'''
CS50 - Project 1
kuneho-yellow
August 16, 2018

Handle routes for the book review web application
'''

import os

from flask import Flask, session, render_template, request, redirect, url_for
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
    # Check if user is already signed in
    if session.get('username') != None:
        return render_template("index.html",
                               loggedin=True,
                               username=session.get("username"),
                               displayname=session.get("displayname"))
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    # GET method should just be the same as index.html
    if request.method == "GET":
        return render_template("index.html")
    
    # Check the form inputs
    username = request.form.get("username")
    password = request.form.get("password")
    displayname = request.form.get("displayname")
    usernameError = "Please enter a username"
    passwordError = "Please enter a password"
    
    # TODO: Check if username and password use all valid characters and length
    if username != "":
        # Check if username already exists
        if db.execute("SELECT * FROM users WHERE username = :username",
                      {"username": username}).rowcount > 0:
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
        # Automatically log in after registration
        session['username'] = username
        if displayname != "":
            session['displayname'] = displayname
        else:
            session['displayname'] = username
        # Redirect to profile page after registration
        return redirect(url_for('profile', session['username']))
    
    # The user didn't enter a valid username or password
    return render_template("index.html",
                           registerusernameerror=usernameError,
                           registerpassworderror=passwordError,
                           registerlastusername=username,
                           registerlastdisplayname=displayname)

@app.route("/login", methods=["GET", "POST"])
def login():
    # GET method should just be the same as index.html
    if request.method == "GET":
        return render_template("index.html")
    
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
        userData = db.execute("SELECT * FROM users WHERE username = :username",
                              {"username": username}).fetchone()
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
        # Save the login info in the session
        session['username'] = userData.username
        if userData.displayname != "":
            session['displayname'] = userData.displayname
        else:
            session['displayname'] = userData.username
        
        # Redirect to profile page after log in
        return redirect(f"/profile/{username}")
    
    # The user didn't enter a valid username or password
    return render_template("index.html",
                           loginusernameerror=usernameError,
                           loginpassworderror=passwordError,
                           loginlastusername=username)

@app.route("/logout")
def logout():
    session.pop('username')
    session.pop('displayname')
    return redirect(url_for('index'))

@app.route("/profile/<string:profilename>")
def profile(profilename):
    # Check if the user of that profile exists
    profileData = db.execute("SELECT * FROM users WHERE username = :username",
                             {"username": profilename}).fetchone()
    error = ""
    profiledisplayname = ""
    if profileData == None:
        error = "User does not exist"
        return render_template("profile.html", error=error)
    elif profileData.displayname != "":
        profiledisplayname = profileData.displayname
    else:
        profiledisplayname = profilename
    
    # Show the username's profile
    return render_template("profile.html",
                           username=session.get("username"),
                           displayname=session.get("displayname"),
                           profilename=profilename,
                           profiledisplayname=profiledisplayname)

@app.route("/books/")
@app.route("/books/allbooks/", defaults={"page": 1})
@app.route("/books/allbooks/<int:page>", methods=["GET"])
def books(page = 1):
    # For browsing the entire book collection
    booksPerPage = 10
    offset = (page - 1) * booksPerPage
    commandStr = f"SELECT * FROM books LIMIT {booksPerPage} OFFSET {offset}"
    books = db.execute(commandStr)
    return render_template("books.html",
                           books=books,
                           username=session.get("username"),
                           displayname=session.get("displayname"))

@app.route("/books/<string:isbn>", methods=["GET"])
def book(isbn):
    # Check if the book woth the given isbn actually exists
    error = ""
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn",
                      {"isbn": isbn}).fetchone()
    if book == None:
        error = "That book is not in our library... Really sorry."
        return render_template("book.html",
                           error=error,
                           username=session.get("username"),
                           displayname=session.get("displayname"))
    
    # Get entries where user rated the specified book
    ratings = db.execute("SELECT rating FROM reviews WHERE isbn = :isbn AND rating > 0",
                            {"isbn": book.isbn})
    # Get the number of ratings
    ratingcount = ratings.rowcount
    # Get the average rating for the book
    rating = 0
    if ratingcount > 1:
        rating = sum(ratings) / ratingcount
        
    # Get entries where user reviewed the specified book
    reviews = db.execute("SELECT username, review FROM reviews WHERE isbn = :isbn AND review IS NOT NULL",
                            {"isbn": book.isbn})
    if reviews.rowcount == 0:
        reviews = None
        
    loggedin = False
    if session.get("username") != None:
        loggedin = True
    
    return render_template("book.html",
                           book=book,
                           rating=rating,
                           ratingcount=ratingcount,
                           reviews=reviews,
                           loggedin=loggedin,
                           username=session.get("username"),
                           displayname=session.get("displayname"))

@app.route("/search", methods=["GET", "POST"])
def search(search = None):
    # Handle searching
    if not search:
        search = request.args.get('search')
    if not search:
        search = request.form.get("search")
    if search:
        # Search books of potentially that isbn / title / author
        # Ordered by book title
        books = db.execute("SELECT * FROM books WHERE title ~* :search OR author ~* :search OR isbn ~* :search ORDER BY title",
                       {"search": search})
    if not search or books.rowcount == 0:
        books = None
    
    return render_template("books.html",
                           search=search,
                           books=books,
                           username=session.get("username"),
                           displayname=session.get("displayname"))