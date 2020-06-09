import os,csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine("postgresql://nzvpobdbklccib:9fa6961f0a96291be84be6ef822b2c5f0be9a2fdfd9414d0efd2a71a4403be65@ec2-54-175-117-212.compute-1.amazonaws.com:5432/dc61mdecpgjv9j")
db = scoped_session(sessionmaker(bind=engine))


def main():
    f = open("books.csv", "r")  # needs to be opened during reading csv
    reader = csv.reader(f)
    next(reader)
    for isbn, title, author, year in reader:
        check_book=db.execute("SELECT *FROM books Where isbn=:isbn",{"isbn":isbn}).fetchall()
        if check_book:
            pass
        else:
            db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
               {"isbn": isbn, "title": title, "author": author, "year": year})
        db.commit()
        print(f"Added book with ISBN: {isbn} Title: {title}  Author: {author}  Year: {year}")


if __name__ == '__main__':
    main()
