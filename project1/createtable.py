from flask import Flask
from flask_sqlalchemy  import SQLAlchemy

db=SQLAlchemy()
app=Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://nzvpobdbklccib:9fa6961f0a96291be84be6ef822b2c5f0be9a2fdfd9414d0efd2a71a4403be65@ec2-54-175-117-212.compute-1.amazonaws.com:5432/dc61mdecpgjv9j"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)#store all data in app

# book tables
class Books(db.Model):
    __tablename__="books"
    bookid=db.Column(db.Integer,primary_key=True , nullable=False)
    isbn=db.Column(db.String, nullable=False)
    title=db.Column(db.String, nullable=False)
    author=db.Column(db.String, nullable=False)
    year=db.Column(db.Integer, nullable=False)


# users table
class Users(db.Model):
    __tablename__="users"
    user_id=db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String, nullable=False)
    username=db.Column(db.String, nullable=False)
    password=db.Column(db.String, nullable=False)

class Reviews(db.Model):
    __tablename__="reviews"
    review_id=db.Column(db.Integer, primary_key=True)
    isbn=db.Column(db.Integer, nullable=False)
    username=db.Column(db.String, nullable=False)
    comment=db.Column(db.String, nullable=False)
    rating=db.Column(db.Integer, nullable=False)

def create():
    db.create_all()
    print("all table created")
if __name__=="__main__":
    with app.app_context():#app_context()
        create()
