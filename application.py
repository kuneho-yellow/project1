'''
CS50 - Project 1
kuneho-yellow
August 16, 2018

Handle routes for the book review web application
'''

import os, requests, math

from flask import Flask, session, render_template, request, redirect, url_for, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from flask_debugtoolbar import DebugToolbarExtension

app = Flask(__name__)

# the toolbar is only enabled in debug mode:
app.debug = True
# set a 'SECRET_KEY' to enable the Flask session cookies
app.config['SECRET_KEY'] = 'justasecretkeythatseasytoguess'
toolbar = DebugToolbarExtension(app)
# Prevent sorting the keys of the json response
app.config['JSON_SORT_KEYS'] = False
# Goodreads api key
goodreadsKey = 'Oo6sL49yEJiiXk4PuMzw'
# Number of books in database
# TODO better, non-slow way to know number of books in entire database
dbBooksTotal = 5000

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
        if not displayname:
            displayname = username
        commandStr = f"INSERT INTO users (username, password, displayname) VALUES ('{username}', '{password}', '{displayname}')"
        # Add the new credentials to the database
        db.execute(commandStr)
        # Automatically log in after registration
        session['username'] = username
        session['displayname'] = displayname
        # Redirect to profile page after registration
        db.commit()
        return redirect(url_for('profile', profilename=session['username']))
    
    # The user didn't enter a valid username or password
    db.commit()
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
        db.commit()
        return redirect(url_for('profile', profilename=session['username']))
    
    # The user didn't enter a valid username or password
    db.commit()
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
    
    if profileData == None:
        db.commit()
        return render_template("profile.html", error="User does not exist")

    # Get the books in this profile
    profilebooks = db.execute("SELECT books.isbn, books.title, books.author, reviews.isbn, reviews.rating, reviews.review FROM reviews, books WHERE reviews.username = :username AND reviews.isbn = books.isbn",
                              {"username": profilename})
    if profilebooks.rowcount == 0:
        profilebooks = None
    
    # Show the username's profile
    db.commit()
    return render_template("profile.html",
                           username=session.get("username"),
                           displayname=session.get("displayname"),
                           profilename=profilename,
                           profiledisplayname=profileData.displayname,
                           profilebooks=profilebooks)


@app.route("/books/")
@app.route("/books/allbooks/", defaults={"page": 1})
@app.route("/books/allbooks/<int:page>", methods=["GET"])
def books(page = 1):
    # For browsing the entire book collection
    booksPerPage = 20
    offset = (page - 1) * booksPerPage
    maxpage = math.ceil(dbBooksTotal / booksPerPage)
    commandStr = f"SELECT * FROM books LIMIT {booksPerPage} OFFSET {offset}"
    books = db.execute(commandStr)
    return render_template("books.html",
                           search=None,
                           pagenumbers=True,
                           books=books,
                           page=page,
                           maxpage=maxpage,
                           username=session.get("username"),
                           displayname=session.get("displayname"))


@app.route("/books/<string:isbn>", methods=["GET", "POST"])
def book(isbn):
    # Check if a user is logged in
    loggedin = False
    if session.get("username") != None:
        loggedin = True
        
    # Check if the book with the given isbn actually exists
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn",
                      {"isbn": isbn}).fetchone()
    # Just display an error message if book does not exist
    if book == None:
        db.commit()
        return render_template("book.html",
                           error="That book is not in our library... Really sorry.",
                           username=session.get("username"),
                           displayname=session.get("displayname"))
    
    # Get the rating and review by the logged in user
    userbookinfo = None
    if loggedin:
        userbookinfo = db.execute("SELECT rating, review FROM reviews WHERE isbn = :isbn AND username = :username",
                            {"isbn": book.isbn, "username": session["username"]}).fetchone()
    
    # Check if the logged in user wants to update his book review
    if loggedin and request.method == 'POST':
        userrating = request.form.get("userrating")
        userreview = request.form.get("userreview")
        if userbookinfo == None:
            # New review/rating entry
            db.execute("INSERT INTO reviews (isbn, username, rating, review) VALUES (:isbn, :username, :rating, :review)",
                       {"isbn": isbn, "username": session["username"], "rating": userrating, "review": userreview})
        else:
            # Update the existing entry
            db.execute("UPDATE reviews SET rating = :rating, review = :review WHERE isbn = :isbn AND username = :username",
                       {"isbn": isbn, "username": session["username"], "rating": userrating, "review": userreview})
        db.commit()
        # Update userbookinfo
        userbookinfo = db.execute("SELECT rating, review FROM reviews WHERE isbn = :isbn AND username = :username",
                            {"isbn": book.isbn, "username": session["username"]}).fetchone()
    
    
    # Get entries where user rated the specified book
    ratings = db.execute("SELECT rating FROM reviews WHERE isbn = :isbn AND rating > 0",
                            {"isbn": book.isbn})
    # Get the number of ratings
    ratingcount = ratings.rowcount
    # Get the average rating for the book
    rating = 0
    if ratingcount > 0:
        for row in ratings:
            rating += row['rating']
        rating /= ratingcount
        
    # Get ratings from Goodreads
    res = requests.get("https://www.goodreads.com/book/review_counts.json",
                       params={"key": goodreadsKey, "isbns": isbn})
    grrating = res.json()["books"][0]['average_rating']
    grratingcount = res.json()["books"][0]['work_ratings_count']

    # Get entries where user reviewed the specified book
    reviews = db.execute("SELECT reviews.username, users.displayname, reviews.rating, reviews.review FROM reviews, users WHERE isbn = :isbn AND review <> '' AND reviews.username = users.username",
                            {"isbn": book.isbn})
    if reviews.rowcount == 0:
        reviews = None
    
    db.commit()
    return render_template("book.html",
                           book=book,
                           rating=rating,
                           ratingcount=ratingcount,
                           grrating=grrating,
                           grratingcount=grratingcount,
                           reviews=reviews,
                           loggedin=loggedin,
                           userbookinfo = userbookinfo,
                           username=session.get("username"),
                           displayname=session.get("displayname"))


@app.route("/search", methods=["GET", "POST"])
def search(search = None, page = 1):
    # Handle searching
    if not search:
        search = request.args.get("search")
        page = request.args.get("page")
    if not search:
        search = request.form.get("search")
        page = request.form.get("page")
    if search:
        if page == None:
            page = 1
        else:
            page = int(page)
        booksPerPage = 20
        offset = (page - 1) * booksPerPage
    
        # Search books of potentially that isbn / title / author
        # Ordered by book title
        books = db.execute("SELECT * FROM books WHERE title ~* :search OR author ~* :search OR isbn ~* :search ORDER BY title LIMIT :booksPerPage OFFSET :offset",
                       {"search": search, "booksPerPage": booksPerPage, "offset": offset})
        error = None
        
    if not search:
        books = None
        error = "Please use the search bar."
    elif books.rowcount == 0 and page == 1:
        books = None
        error = "No books found... Really sorry."
    elif books.rowcount == 0 and page > 1:
        error = "No other books found."
        # If there are no more results found, load the last page result
        while (books.rowcount == 0 and page > 1):
            page -= 1
            offset = (page - 1) * booksPerPage
            books = db.execute("SELECT * FROM books WHERE title ~* :search OR author ~* :search OR isbn ~* :search ORDER BY title LIMIT :booksPerPage OFFSET :offset",
                       {"search": search, "booksPerPage": booksPerPage, "offset": offset})
        if books.rowcount == 0:
            books = None
            error = "No books found... Really sorry."
    
    db.commit()
    return render_template("books.html",
                           error=error,
                           search=search,
                           books=books,
                           pagenumbers=False,
                           page=page,
                           username=session.get("username"),
                           displayname=session.get("displayname"))
    

@app.route("/api/<string:isbn>")
def api(isbn):
    # Create the dictionary to form the JSON object
    bookjson = {}
    
    # Check if the book with the given isbn actually exists
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn",
                      {"isbn": isbn}).fetchone()
    # Just display an error message if book does not exist
    if book == None:
        return "That book is not in our library... Really sorry."
    
    # Get entries where user rated the specified book
    ratings = db.execute("SELECT rating FROM reviews WHERE isbn = :isbn AND rating > 0",
                            {"isbn": book.isbn})
    # Get the number of ratings
    ratingcount = ratings.rowcount
    # Get the average rating for the book
    rating = 0
    if ratingcount > 0:
        for row in ratings:
            rating += row['rating']
        rating /= ratingcount
    
    bookjson["title"] = book.title
    bookjson["author"] = book.author
    bookjson["year"] = book.year
    bookjson["isbn"] = isbn
    bookjson["review_count"] = ratingcount
    bookjson["average_score"] = rating
    
    return jsonify(bookjson)
