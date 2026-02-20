from datetime import date
from typing import Optional

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, Book
from app.settings import DATABASE_URL

# DISCLAIMER:
# This is a very simple CRUD API
# Not intended for production


import time
from sqlalchemy.exc import OperationalError

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


def recreate_database():
    max_retries = 5
    retry_delay = 3

    for i in range(max_retries):
        try:
            print(f"Connecting to database (attempt {i + 1}/{max_retries})...")
            # Base.metadata.drop_all(engine)
            Base.metadata.create_all(engine)
            print("Database connected and tables created!")
            break
        except OperationalError as e:
            if i == max_retries - 1:
                print("Could not connect to database after several attempts.")
                raise e
            print(f"Database not ready yet, retrying in {retry_delay}s...")
            time.sleep(retry_delay)


recreate_database()


app = FastAPI()


@app.get("/")
def root():
    return {"message": "Sample books API is online"}


@app.post("/books")
def create_book(title: str, pages: int):
    session = Session()
    book = Book(title=title, pages=pages, created_at=date.today())
    session.add(book)
    session.commit()
    session.close()

    return JSONResponse(
        status_code=200, content={"status_code": 200, "message": "success"}
    )


@app.get("/books/{id}")
def find_book(id: int):
    session = Session()
    book = session.query(Book).filter(Book.id == id).first()
    session.close()

    result = jsonable_encoder({"book": book})

    return JSONResponse(status_code=200, content={"status_code": 200, "result": result})


@app.get("/books")
def get_books(page_size: int = 10, page: int = 1):
    if page_size > 100 or page_size < 0:
        page_size = 100

    session = Session()
    books = session.query(Book).limit(page_size).offset((page - 1) * page_size).all()
    session.close()

    result = jsonable_encoder({"books": books})

    return JSONResponse(status_code=200, content={"status_code": 200, "result": result})


@app.put("/books")
def update_book(id: int, title: Optional[str] = None, pages: Optional[int] = None):
    session = Session()
    book = session.query(Book).get(id)
    if title is not None:
        book.title = title
    if pages is not None:
        book.pages = pages
    session.commit()
    session.close()

    return JSONResponse(
        status_code=200, content={"status_code": 200, "message": "success"}
    )


@app.delete("/books")
def delete_book(id: int):
    session = Session()
    book = session.query(Book).get(id)
    session.delete(book)
    session.commit()
    session.close()

    return JSONResponse(
        status_code=200, content={"status_code": 200, "message": "success"}
    )


@app.exception_handler(Exception)
def exception_handler(request, exc):
    json_resp = get_default_error_response()
    return json_resp


def get_default_error_response(status_code=500, message="Internal Server Error"):
    return JSONResponse(
        status_code=status_code,
        content={"status_code": status_code, "message": message},
    )
