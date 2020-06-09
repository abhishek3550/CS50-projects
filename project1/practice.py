from model import *
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

engine = create_engine("postgresql://abhishek:welcome1234@127.0.0.1:5432/mydb")
db=scoped_session(sessionmaker(bind=engine))
'''
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
'''

app.permanent_session_lifetime = timedelta(days=1)
app.secret_key = 'flask'

# login system logic starts here
@app.route('/')
def signin():
    if 'fullname' in session:
        flash('Already Signed in')
        return redirect(url_for('home',alert='Already Signed in'))
    else:
        return render_template('login.html')


@app.route('/signin_validation', methods=["POST", "GET"])
def signin_validation():
    if request.method == 'POST':
        username = request.form['loginusername']
        password = request.form['loginpassword']

        # check if password match with database
        check_user = db.execute("select * from public.users where username = :username", {'username': username}).fetchone()

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


@app.route('/home')
def home():
    if 'username' in session:
        username = session['username']
        db_user_query = db.execute("select * from users where username = :username", {'username': username}).fetchall()
        db_review_query = db.execute(" select * from reviews where username = :username", {'username': username}).fetchall()
        # root = request.url_root()
        fullname=username
        userInfo = {
            'user_id':db_user_query[0][0],
            'fullname': db_user_query[0][1],
            'username': session['username'],
            'password': db_user_query[0][3],
        }
        reviewCount = len(db_review_query)

        return render_template('index.html', userInfo=userInfo, reviewedbooks=db_review_query, reviewCount=reviewCount)

    else:
        flash('Sign first')
        return redirect(url_for('signin',alert='Signin First'))


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        # get info from user input
        fullname = request.form['fullname']
        username = request.form['username']
        password = request.form['password']

        # check if the email is already in the table
        check_user = db.execute("select * from public.users where username = :username", {'username': username}).fetchall()

        if check_user:
            flash('You are already registed.')
            return redirect(url_for('signin',alert='You are already registed'))
        else:
            # add a new user in database
            db.execute("INSERT INTO public.users (fullname, username, password) VALUES (:fullname, :username , :password)", {
                "fullname": fullname, "username": username, "password": password})
            db.commit()

            # save the data in session
            session['fullname'] = fullname
            session['username'] = username
            session['password'] = password

            flash('Registraion successful')
            return redirect(url_for('home'))
    else:
        if 'name' in session:
            flash('You are Already registered ')
            return redirect(url_for('home', alert='You are already registed'))
        else:
            return render_template('login.html')


@app.route('/signout')
def signout():
    if 'fullname' in session:
        session.pop('fullname', None)
        session.pop('username', None)
        session.pop('password', None)

        flash('Signed out successfully', 'info')
        return redirect(url_for('signin',alert='Signed out successfully '))
    else:
        flash('Already Singed out')
        return redirect(url_for('signin',alert='Already Singed out'))

@app.route('/book',methods=['GET','POST'])
def search():
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
            text = title
        elif author:
            result = db.execute(" SELECT * FROM books WHERE author LIKE '%"+author+"%' ;").fetchall()
            text = author
        elif year:
            result = db.execute(" SELECT * FROM books WHERE year = :year", {'year':year}).fetchall()
            text = year
        else:
            result = db.execute(" SELECT * FROM books WHERE isbn LIKE '%"+isbn+"%' ;").fetchall()
            text = isbn

        #if found then save it in list
        if result:
            for i in result :
                list.append(i)
            itemsCount = len(list)
            return render_template('search.html', baseUrl = baseUrl,  items = list, msg = "Yei ! Search result found", text = text , itemsCount = itemsCount)

        #if not found show a not found message
        else:
            return render_template('search.html', msgNo = "Sorry! No books found" , text = text)



    return render_template ('search.html')


@app.route('/book/<string:isbn>', methods = ['GET', 'POST'])
def thebook(isbn):
    isbn=isbn
    username=session['username']

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
        # api=json.dumps(x)
        # return render_template("api.json",api=api)
        return  jsonify(x)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html'), 404



if __name__=="__main__":
    app.run(debug=True)



'''

@app.route("/details/<int:bookid>", methods=["GET","POST"])
def details(bookid):
    if request.method == "GET":
        #Get book details
        result = db.execute("SELECT * from books WHERE bookid = :bookid", {"bookid": bookid}).fetchone()

        #Get API data from GoodReads
        try:
            goodreads = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": key, "isbns": result.isbn})
        except Exception as e:
            return render_template("error.html", message = e)

        # Get comments particular to one book
        comment_list = db.execute("SELECT u.firstname, u.lastname, u.email, r.rating, r.comment from reviews r JOIN users u ON u.userid=r.user_id WHERE book_id = :id", {"id": bookid}).fetchall()
        if not result:
            return render_template("error.html", message="Invalid book id")

        return render_template("details.html", result=result, comment_list=comment_list , bookid=bookid, goodreads=goodreads.json()["books"][0])
    else:
        ######## Check if the user commented on this particular book before ###########
        user_reviewed_before = db.execute("SELECT * from reviews WHERE user_id = :user_id AND book_id = :book_id",  {"user_id": session["user_id"], "book_id": bookid}).fetchone()
        if user_reviewed_before:
            return render_template("error.html", message = "You reviewed this book before!")
        ######## Proceed to get user comment ###########
        user_comment = request.form.get("comments")
        user_rating = request.form.get("rating")

        if not user_comment:
            return render_template("error.html", message="Comment section cannot be empty")

        # try to commit to database, raise error if any
        try:
            db.execute("INSERT INTO reviews (user_id, book_id, rating, comment) VALUES (:user_id, :book_id, :rating, :comment)",
                           {"user_id": session["user_id"], "book_id": bookid, "rating":user_rating, "comment": user_comment})
        except Exception as e:
            return render_template("error.html", message=e)

        #success - redirect to details page
        db.commit()
        return redirect(url_for("details", bookid=bookid))
'''