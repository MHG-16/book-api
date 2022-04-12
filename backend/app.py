from datetime import datetime, timezone
from heapq import nlargest
from http.client import responses
from flask import Flask, request
from flask_restx import Api, Resource, fields
from flask_sqlalchemy import SQLAlchemy
import os

basedir = os.path.dirname(os.path.realpath("__file__"))

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "books.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True

api = Api(app, doc="/", title="api book", description = "simple api book")

db = SQLAlchemy(app)

parser = api.parser()
parser.add_argument('title', type=str, location="title")
parser.add_argument('author', type=str, location="author")


class Book(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String(65), nullable=False)
    author = db.Column(db.String(40), nullable=False)
    date_added = db.Column(db.DateTime(), default=datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return self.title


book_model = api.model(
    "Book",
    {
        "title": fields.String(required=True),
        "author": fields.String(required=True),
        "date_join": fields.String(),
    },
)

book_ns = api.namespace("book" , description="book requests")

@book_ns.route("/books")
class Books(Resource):
    @api.doc(responses = {
        400:"Error connection database"
    })
    @api.marshal_list_with(book_model, code=200, envelope="books")
    def get(self):
        '''get all books'''
        books = Book.query.all()
        return books

    @api.marshal_with(book_model, code=201, envelope="book")
    @api.doc(responses={
        400:"Error register database"
    })
    @api.expect(book_model)
    @api.doc(responses={
        400:"Error connection database"
    })
    def post(self):
        '''add one book'''
        data = request.get_json()
        print(data)
        title = data.get("title")
        author = data.get("author")

        new_book = Book(title=title, author=author)
        db.session.add(new_book)
        db.session.commit()

        return new_book


@book_ns.route("/book<int:id>")
class BookResource(Resource):
    @api.marshal_with(book_model, code=200, envelope="book")
    @api.doc(responses={
        400:"Error connection database"
    })
    def get(self, id):
        '''get a book by id'''
        book = Book.query.get_or_404(id)
        return book

    @api.marshal_with(book_model, code=200, envelope="book")
    @api.doc(responses={
        400:"Error connection database"
    })
    def put(self, id):
        '''put a book by id'''
        book_to_update = Book.query.get_or_404(id)

        data = request.get_json()
        book_to_update.title = data.get("title")
        book_to_update.author = data.get("author")

        db.session.commit()

        return book_to_update

    @api.marshal_with(book_model, code=200, envelope="book deleted")
    @api.doc(responses={
        400:"Error connection database"
    })
    def delete(self, id):
        '''delete a book by id'''
        book_to_delete = Book.query.get_or_404(id)

        db.session.delete(book_to_delete)
        db.session.commit()
        
        return book_to_delete, 200


@app.shell_context_processor
def make_shell_context():
    return {"db": db, "Book": Book}


if __name__ == "__main__":
    app.run(debug=True)
