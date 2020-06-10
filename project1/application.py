from flask import Flask,render_template,request,session,flash,redirect,url_for
from sqlalchemy import create_engine
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_session import Session
from datetime import timedelta
import requests
import json
from flask import jsonify



app=Flask(__name__)

engine = create_engine("postgresql://username:password@host:port/databasename")
db=scoped_session(sessionmaker(bind=engine))

#session time last for 1 day only
app.permanent_session_lifetime = timedelta(days=1)
app.secret_key = 'pathshala'

# login page
@app.route('/')
def signin():
    if 'fullname' in session:
        flash('Already Signed in')
        return redirect(url_for('home',alert='Already Signed in'))
    else:
        return render_template('login.html')

#login validation
@app.route('/signin_validation', methods=["POST", "GET"])
def signin_validation():
    if request.method == 'POST':
        username = request.form['loginusername']
        password = request.form['loginpassword']

        # check if password match with database
        check_user = db.execute("select * from users where username = :username", {'username': username}).fetchone()
        #check user is in data base
        if check_user:
            list = []
            for i in check_user:
                list.append(i)

            check_user_id = list[0]
            check_fullname = list[1]
            check_username = list[2]
            check_pass = list[3]
            if check_username == username  and check_pass == password:
                session.permanent = True
                session['user_id'] = check_user_id
                session['fullname'] = check_fullname
                session['username'] = check_username
                session['password'] = check_pass
                flash('Signin successful')
                return redirect(url_for('home',alert={check_fullname}))
            else:
                flash('User name or password is incorrect')
                return redirect(url_for('signin' ,alert='User name or password is incorrect'))
        else:
            flash('You are not registed in this website. Please register first.')
            return redirect(url_for('signin',alert='You are not registed in this website. Please register first.'))
    else:
        flash('Signin failed')
        return redirect(url_for('signin',alert='Signin failed'))

#homepage session
@app.route('/home')
def home():
    if 'username' in session:
        username = session['username']
        db_user_query = db.execute("select * from users where username = :username", {'username': username}).fetchall()
        db_review_query = db.execute(" select * from reviews where username = :username", {'username': username}).fetchall()
        fullname=username
        userInfo = {
            'fullname': db_user_query[0][1],
            'username': session['username'],
            'password': db_user_query[0][3],
        }
        reviewCount = len(db_review_query)

        return render_template('index.html', userInfo=userInfo, reviewedbooks=db_review_query, reviewCount=reviewCount)

    else:
        flash('Sign first')
        return redirect(url_for('signin',alert='Signin First'))

#new user registeration
@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        # get info from user input
        fullname = request.form['fullname']
        username = request.form['username']
        password = request.form['password']

        # check if the username is already in the users table
        check_user = db.execute("select * from public.users where username = :username", {'username': username}).fetchall()

        if check_user:
            flash('You are already registed.')
            return redirect(url_for('signin'))
        else:
            #Adding a new user in database
            db.execute("INSERT INTO public.users (fullname, username, password) VALUES (:fullname, :username , :password)", {
                "fullname": fullname, "username": username, "password": password})
            db.commit()

            # save the data in session and redirect user to homepage
            session['fullname'] = fullname
            session['username'] = username
            session['password'] = password

            flash('Registraion successful')
            return redirect(url_for('home'))
    else:
        if 'fullname' in session:
            flash('You are Already registered ')
            return redirect(url_for('home'))
        else:
            return render_template('login.html')

#removing user session by singout
@app.route('/Logout')
def Logout():
    if 'fullname' in session:
        session.pop('fullname', None)
        session.pop('username', None)
        session.pop('password', None)

        flash('Signed out successfully', 'info')
        return redirect(url_for('signin'))
    else:
        flash('Already Singed out')
        return redirect(url_for('signin'))
#search page
@app.route('/book',methods=['GET','POST'])
def search():
    #if post get input from form
    if request.method == "POST":
        title = request.form['byTitle']
        title = title.title()
        author = request.form['byAuthor']
        year = request.form['byYear']
        isbn = request.form['byIsbn']

        list = []
        text = None
        baseUrl= request.base_url
        if title:
            result = db.execute(" SELECT * FROM books WHERE title LIKE '%"+title+"%' ;").fetchall()

        elif author:
            result = db.execute(" SELECT * FROM books WHERE author LIKE '%"+author+"%' ;").fetchall()

        elif year:
            result = db.execute(" SELECT * FROM books WHERE year = :year", {'year':year}).fetchall()

        else:
            result = db.execute(" SELECT * FROM books WHERE isbn LIKE '%"+isbn+"%' ;").fetchall()


        #if found then save it in list
        if result:
            for i in result :
                list.append(i)
            itemsCount = len(list)
            return render_template('search.html', baseUrl = baseUrl,  items = list, itemsCount = itemsCount)

        #if not found show a not found message
        else:
            flash("NO Book Found")
            return render_template('search.html')

    return render_template ('search.html')

#review page and submission
@app.route('/book/<string:isbn>', methods = ['GET', 'POST'])
def thebook(isbn):
    isbn=isbn
    username=session['username']
    #api requested
    api = requests.get("https://www.goodreads.com/book/review_counts.json",params={"key": "M8gFztxMpErAAy94QEw", "isbns": isbn})
    # print(res.json())
    apidata = api.json()
    booktable=db.execute('SELECT * FROM books WHERE isbn = :isbn',{"isbn": isbn}).fetchall()
    reviewstable=db.execute('SELECT * FROM reviews WHERE isbn= :isbn',{"isbn": isbn}).fetchall()
    alreadyreviewed=db.execute('SELECT * FROM reviews WHERE isbn= :isbn AND username= :username',{"isbn":isbn, "username": username}).fetchall()
    if request.method == 'POST':
        if alreadyreviewed:
            flash('You alreaddy submitted a review on this book')
        else:
            rating = int(request.form['rating'])
            comment = request.form['comment']
            username = session['username']
            fisbn = request.form['isbn']
            db.execute(
                "INSERT into reviews (username, rating, comment, isbn) Values (:username, :rating, :comment, :isbn)",
                {'username': username, 'rating': rating, 'comment': comment, 'isbn': fisbn})
            db.commit()
            flash('Awesome, Your review added successfully ')

    if api:
        return render_template('thebook.html', apidata=apidata, booktable=booktable, reviewstable=reviewstable, isbn=isbn)
    else:
        flash('Data fetch failed')
        return render_template('thebook.html')

#JSON response
@app.route("/book/api/<string:isbn>")
def api(isbn):
    if 'username' in session:
        data=db.execute("SELECT * FROM public.books WHERE isbn = :isbn",{"isbn":isbn}).fetchone()
        if data==None:
            return render_template('error.html')
        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "M8gFztxMpErAAy94QEw", "isbns": isbn})
        average_rating=res.json()['books'][0]['average_rating']
        work_ratings_count=res.json()['books'][0]['work_ratings_count']
        x = {
        "title": data.title,
        "author": data.author,
        "year": data.year,
        "isbn": isbn,
        "review_count": work_ratings_count,
        "average_rating": average_rating
        }
        return  jsonify(x)

#Registering error handler to 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html'), 404

if __name__=="__main__":
    app.run(debug=True)


