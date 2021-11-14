from flask import Flask, session, request
from flask.ext.session import Session
import sqlite3


app = Flask(__name__)

con = sqlite3.connect('rateIt.db')
cur = con.cursor()

SESSION_TYPE = 'mongodb'
app.config.from_object(__name__)
Session(app)


@app.route('/login')
def login():
    session['logged_in'] = True

@app.route("/get/likes")
def getLikes():
    url = request.args.get('url')

@app.route("/get/dislikes")
def getDislikes():
    url = request.args.get('url')

@app.route("/post/like")
def postLike():
    url = request.args.get('url')
    loggedIn = session.get('logged_in')

@app.route("/post/dislike")
def postDislike():
    url = request.args.get('url')
    loggedIn = session.get('logged_in')