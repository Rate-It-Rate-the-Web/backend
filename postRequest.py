from flask import Flask, request, session
import rateIt
import db
import requests


@rateIt.app.route('/login', methods=['POST'])
def login():
    token = request.json["token"]
    validToken = rateIt.verifyOauth(token)
    if validToken:
        userinfo = requests.get("https://www.googleapis.com/oauth2/v1/userinfo",
                                params={"alt": "json", "access_token": token}).json()
        id = userinfo["id"]
        if db.checkGoogleUser(id):
            session["logged_in"] = True
            session["userId"] = db.scanItem(
                db.userTable, 'googleUserId', id)["userId"]
            return "success"
        else:
            db.createUser(id, userinfo["given_name"])
            session["logged_in"] = True
            session["userId"] = db.scanItem(
                db.userTable, 'googleUserId', id)["userId"]
            return "success"
    else:
        return "invalid token"


@rateIt.app.route("/post/rating", methods=['POST'])
def postRating():
    content = request.json
    user = session["userId"]
    url = content["url"].lower()
    if session["logged_in"] and db.checkUser(user):
        if content["rating"] == 1:
            if db.checkUrlDisliked(url, user):
                db.incrementDisLikes(url, -1, user)
            if not db.checkUrlLiked(url, user):
                db.incrementLikes(url, 1, user)
        elif content["rating"] == -1:
            if db.checkUrlLiked(url, user):
                db.incrementLikes(url, -1, user)
            if not db.checkUrlDisliked(url, user):
                db.incrementDisLikes(url, 1, user)
        elif content["rating"] == 0:
            if db.checkUrlLiked(url, user):
                db.incrementLikes(url, -1, user)
            if db.checkUrlDisliked(url, user):
                db.incrementDisLikes(url, -1, user)

        return "success"
    else:
        return "not logged in"
