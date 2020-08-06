import os
import re
import io 
import base64
import mysql.connector
import qrcode

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from io import BytesIO
from helpers import apology, login_required

# export FLASK_APP='app.py'

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure MySQL
def getconnection():
    db = mysql.connector.connect(
        host="MYSQL5006.site4now.net",
        user="9d6e6e_ronify",
        password="Ronify@2020",
        database="db_9d6e6e_ronify"
    )
    return db

@app.route("/")
def index(): 
    
    db = getconnection()
    cur = db.cursor()
    
    cur.execute("SELECT count(*) FROM business") 
    bcount = cur.fetchall()
    
    cur.execute("SELECT count(*) FROM visitor") 
    vcount = cur.fetchall()
    
    cur.close()
    db.close()

    return render_template("index.html", bcount=bcount[0][0], vcount=vcount[0][0])


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure email was submitted
        if not request.form.get("email"):
            return apology("must provide email", 403)

        # Ensure password was email
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        db = getconnection()
        cur = db.cursor()

        # Query database for password based on user's email
        cur.execute("SELECT id, passwordhash FROM business WHERE email = %s", (request.form.get("email"), ))
        rows = cur.fetchall()
        user_id = rows[0][0]
        p_hash = rows[0][1]

        cur.close()
        db.close()

        # Ensure email exists and password is correct
        if len(rows) != 1 or not check_password_hash(p_hash, request.form.get("password")):
            return apology("invalid email and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = user_id

        # Redirect user to home page
        return redirect("/dashboard")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("name"):
            return apology("must provide a company name", 403)

        # Ensure email was submitted
        elif not request.form.get("email"):
            return apology("must provide email", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Ensure confirmation password was submitted
        elif not request.form.get("confirm"):
            return apology("must provide a confirmation password", 403)

        # Ensure the password and confirmation password match
        elif request.form.get("password") != request.form.get("confirm"):
            return apology("password and confirmation do not match", 403)

        db = getconnection()
        cur = db.cursor()

        # Creating unique code from business name
        name = request.form.get("name").strip()
        code = re.sub('[^A-Za-z0-9]+', '', name)

        i = 0
        while True:          
            cur.execute("SELECT count(*) FROM business WHERE code = %s", (code, ))
            repeat = cur.fetchall()
            if repeat[0][0] > 0:
                if i > 0:
                    code = code[:-1]
                i += 1
                code = code + str(i)
            else:
                break

        # Insert company name, email, and password hash into database
        query = "INSERT INTO business (name, code, email, passwordhash, created_at) VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)"
        values = (name, code, request.form.get("email"), generate_password_hash(request.form.get("password")))

        cur.execute(query, values)

        # Remember that the new user has logged in
        session["user_id"] = cur.lastrowid

        cur.close()
        db.close()

        # Redirect user to home page
        return redirect("/dashboard")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/business/<code>", methods=["GET", "POST"])
def business(code):
    """Customer form"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure a name was submitted
        if not request.form.get("name"):
            return apology("must provide a name", 403)

        # Ensure phone number was submitted
        elif not request.form.get("phone"):
            return apology("must provide a phone number", 403)
        
        # Ensure number of guests was submitted
        elif not request.form.get("guests"):
            return apology("must provide number of guests", 403)
        
        db = getconnection()
        cur = db.cursor()

        cur.execute("SELECT id FROM business WHERE code = %s", (code, ))
        business_id = cur.fetchall()

        # determines if business id exists for the passed code
        business_id = business_id[0][0]

        # Insert name, phone number, email, guests, and time into customers database
        query = "INSERT INTO visitor (business_id, name, phone, email, guests, created_at) VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)"
        values = (business_id, request.form.get("name"), request.form.get("phone"), request.form.get("email"), request.form.get("guests"))

        cur.execute(query, values)

        # Redirect user to home page
        if session["user_id"]:
            return redirect("/dashboard")
        else:
            cur.execute("SELECT name FROM business WHERE code = %s", (code, ))
            business_name = (cur.fetchall())[0][0]
            
            return render_template("thankyou.html", name=business_name)
        
        cur.close()
        db.close()

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        
        db = getconnection()
        cur = db.cursor()

        cur.execute("SELECT name FROM business WHERE code = %s", (code, ))
        name = cur.fetchall()

        # passing through business name
        name = name[0][0]

        cur.close()
        db.close()

        return render_template("business.html", name=name, code=code)


@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():

    db = getconnection()
    cur = db.cursor()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        
        if "hour" in request.form:
            cur.execute("SELECT name, phone, email, guests, created_at FROM visitor WHERE business_id = %s AND created_at >= DATE_SUB(NOW(),INTERVAL 1 HOUR) ORDER BY created_at DESC", (session["user_id"], ))
        elif "day" in request.form:
            cur.execute("SELECT name, phone, email, guests, created_at FROM visitor WHERE business_id = %s AND created_at >= DATE_SUB(NOW(),INTERVAL 1 DAY) ORDER BY created_at DESC", (session["user_id"], ))
        elif "week" in request.form:
            cur.execute("SELECT name, phone, email, guests, created_at FROM visitor WHERE business_id = %s AND created_at >= DATE_SUB(NOW(),INTERVAL 1 WEEK) ORDER BY created_at DESC", (session["user_id"], ))

        rows = cur.fetchall()

        cur.execute("SELECT name FROM business WHERE id = %s", (session["user_id"], ))
        name = (cur.fetchall())[0][0]

        cur.execute("SELECT code FROM business WHERE id = %s", (session["user_id"], ))
        code = (cur.fetchall())[0][0]


        return render_template("dashboard.html", rows=rows, name=name, code=code)

    else:

        cur.execute("SELECT name, phone, email, guests, created_at FROM visitor WHERE business_id = %s ORDER BY created_at DESC", (session["user_id"], ))
        rows = cur.fetchall()

        cur.execute("SELECT name FROM business WHERE id = %s", (session["user_id"], ))
        name = (cur.fetchall())[0][0]

        cur.execute("SELECT code FROM business WHERE id = %s", (session["user_id"], ))
        code = (cur.fetchall())[0][0]

        return render_template("dashboard.html", rows=rows, name=name, code=code)

    cur.close()
    db.close()


@app.route("/qrcode", methods=["GET"])
@login_required
def qr_code():

    db = getconnection()
    cur = db.cursor()

    cur.execute("SELECT name FROM business WHERE id = %s", (session["user_id"], ))
    name = (cur.fetchall())[0][0]

    cur.execute("SELECT code FROM business WHERE id = %s", (session["user_id"], ))
    code = (cur.fetchall())[0][0]

    cur.close()
    db.close()
    
    # Generate QR Code
    qrimg = qrcode.make('https://yesleaf.com/ronify/business/' + code)

    buffered = BytesIO()
    qrimg.save(buffered, format='png')
    img_str = base64.b64encode(buffered.getvalue()).decode()

    return render_template("qrcode.html", name=name, imgstr=img_str)

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
