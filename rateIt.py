from flask import Flask, request, session
import requests
import db
from datetime import timedelta

app = Flask(__name__)

app.secret_key = 'dev'
SESSION_TYPE = 'filesystem'
app.config.from_object(__name__)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=182)

empty = {'likes': 0, 'dislikes': 0, 'userRating': 0}
db.appendAnswer('https%3A%2F%2Fwww.youtube.com%2F', "5abefd2b-b321-43b5-a7a9-d6825d6bed15", {'content': 'test', 'userId': '3bfeb2c9-5263-47d9-ae45-547d797a2057', 'answers': []})
def verifyOauth(accessToken):
    # verify if access token is valid
    response = requests.get(
        "https://www.googleapis.com/oauth2/v1/tokeninfo", params={"access_token": accessToken})
    if response.status_code == 200:
        return True
    else:
        return False


@app.route('/login', methods=['POST'])
def login():
    session.permanent = True
    token = request.json["token"]
    validToken = verifyOauth(token)
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


@app.route("/post/rating", methods=['POST'])
def postRating():
    content = request.json
    user = session["userId"]
    print(user)
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


@app.route("/get/rating")
def getRating():
    url = request.args.get('url').lower()
    rating = rating = db.queryItem(db.ratingTable, 'url', url)
    if rating == False:
        return empty
    try:
        rating["userRating"] = (1 if db.checkUrlLiked(
            url, session["userId"]) else (-1 if db.checkUrlDisliked(url, session["userId"]) else 0))
    except:
        pass

    return rating


if __name__ == "__main__":
    app.run()
"""
sudo dynamodb

aws dynamodb create-table --table-name rateIt --attribute-definitions AttributeName=url,AttributeType=S --key-schema AttributeName=url,KeyType=HASH --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=10 --endpoint-url http://localhost:8000

aws dynamodb create-table --table-name users --attribute-definitions AttributeName=userId,AttributeType=S --key-schema AttributeName=userId,KeyType=HASH --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=10 --endpoint-url http://localhost:8000

"""
