from flask import Flask, session, request
from flask_session import Session
import boto3
from boto3.dynamodb.conditions import Key
import requests
import uuid
from decimal import Decimal

from requests.api import put

app = Flask(__name__)

app.secret_key = 'dev'
SESSION_TYPE = 'filesystem'
app.config.from_object(__name__)
Session(app)
db = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")
ratingTable = db.Table('rateIt')
userTable = db.Table('users')


empty = {'likes': 0, 'dislikes': 0, 'userRating': 0}

def putItem(table, item):
    table.put_item(Item=item)


def incrementValue(table, key, keyToIncrement, valueToIncrement, increment):
    # increment value of key in db
    table.update_item(Key={key: keyToIncrement},
                      UpdateExpression="set " + valueToIncrement + " = "+valueToIncrement+" + :val",
                      ExpressionAttributeValues={':val': increment})


def appendToSet(table, key, keyToAppend, setToCreate, appendVal):
    # append to list in db
    try:
        table.update_item(Key={key: keyToAppend},
                          UpdateExpression="add " + setToCreate + " :val",
                          ExpressionAttributeValues={':val': set([appendVal])})
    except:
        table.update_item(Key={key: keyToAppend},
                          UpdateExpression="add " + setToCreate + " :val",
                          ExpressionAttributeValues={':val': set([appendVal])})


def removeFromSet(table, key, keyToDelete, setToRemove, valueToDelete):
    # remove value from list in db
    table.update_item(Key={key: keyToDelete},
                      UpdateExpression="delete " + setToRemove + " :val",
                      ExpressionAttributeValues={':val': set([valueToDelete])})


def incrementLikes(url, number, userId):
    # increment likes for url
    if not queryItem(ratingTable, 'url', url):
        putItem(ratingTable, {"url": url, "likes": 0, "dislikes": 0})
    incrementValue(ratingTable, 'url', url, 'likes', number)
    # add url to liked urls for user
    if number == 1:
        appendToSet(userTable, 'userId', userId, 'likedUrls', url)
    elif number == -1:
        removeFromSet(userTable, 'userId', userId, 'likedUrls', url)


def incrementDisLikes(url, number, userId):

    if not queryItem(ratingTable, 'url', url):
        putItem(ratingTable, {"url": url, "likes": 0, "dislikes": 0})
    # increment dislikes for url
    incrementValue(ratingTable, 'url', url, 'dislikes', number)
    # add url to disliked urls for user
    if number == 1:
        appendToSet(userTable, 'userId', userId, 'dislikedUrls', url)
    else:
        removeFromSet(userTable, 'userId', userId, 'dislikedUrls', url)


def updateItem(table, key, value, update):
    # update item in db
    table.update_item(Key={key: value}, UpdateExpression=update)


def queryItem(table, key, value):
    # query item which url=value from table
    try:
        response = table.query(KeyConditionExpression=Key(key).eq(value))
        return response['Items'][0]
    except:
        return False


def scanItem(table, key, value):
    # scan table for item with key=value
    try:
        response = table.scan(FilterExpression=Key(key).eq(value))
        return response['Items'][0]
    except:
        return False


def createUser(googleUserId, username):
    # create new user in db
    uuid_string = str(uuid.uuid4())
    session["userId"] = uuid_string
    putItem(userTable, {'googleUserId': googleUserId,
            'username': username, 'userId': uuid_string})


def checkGoogleUser(googleUserId):
    # check if user exists in db
    user = scanItem(userTable, 'googleUserId', googleUserId)
    if not user:
        return False
    else:
        return True


def checkUser(uuid_string):
    # check if user exists in db
    user = queryItem(userTable, 'userId', uuid_string)
    if user:
        return True
    else:
        return False


def checkUrlLiked(url, userId):
    # check if user has liked url
    user = queryItem(userTable, 'userId', userId)
    try:
        if url in user['likedUrls']:
            return True
        else:
            return False
    except: 
        return False

def checkUrlDisliked(url, userId):
    # check if user has disliked url
    user = queryItem(userTable, 'userId', userId)
    try:
        if url in user['dislikedUrls']:
            return True
        else:
            return False
    except:
        return False


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
    token = request.json["token"]
    validToken = verifyOauth(token)
    if validToken:
        userinfo = requests.get("https://www.googleapis.com/oauth2/v1/userinfo",
                                params={"alt": "json", "access_token": token}).json()
        id = userinfo["id"]
        if checkGoogleUser(id):
            session["logged_in"] = True
            session["userId"] = scanItem(
                userTable, 'googleUserId', id)["userId"]
            return "success"
        else:
            createUser(id, userinfo["given_name"])
            session["logged_in"] = True
            session["userId"] = scanItem(
                userTable, 'googleUserId', id)["userId"]
            return "success"
    else:
        return "invalid token"


@app.route("/get/rating")
def getRating():
    url = request.args.get('url').lower()
    rating = queryItem(ratingTable, 'url', url)
    try:
        rating["userRating"] = (1 if checkUrlLiked(url, session["userId"]) else (-1 if checkUrlDisliked(url, session["userId"]) else 0))
    except:
        return empty
    return rating


@app.route("/post/rating", methods=['POST'])
def postRating():
    content = request.json
    user = session["userId"]
    url = content["url"].lower()
    if session["logged_in"] and checkUser(user):
        if content["rating"] == 1:
            if checkUrlDisliked(url, user):
                incrementDisLikes(url, -1, user)
            if checkUrlLiked(url, user):
                incrementLikes(url, 1, user)
        elif content["rating"] == -1:
            if checkUrlLiked(url, user):
                incrementLikes(url, -1, user)
            if checkUrlDisliked(url, user):
                incrementDisLikes(url, 1, user)
        elif content["rating"] == 0:
            if checkUrlLiked(url, user):
                incrementLikes(url, -1, user)
            if checkUrlDisliked(url, user):
                incrementDisLikes(url, -1, user)

        return "success"
    else:
        return "not logged in"


if __name__ == "__main__":
    app.run()
"""
sudo dynamodb

aws dynamodb create-table --table-name rateIt --attribute-definitions AttributeName=url,AttributeType=S --key-schema AttributeName=url,KeyType=HASH --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=10 --endpoint-url http://localhost:8000

aws dynamodb create-table --table-name users --attribute-definitions AttributeName=userId,AttributeType=S --key-schema AttributeName=userId,KeyType=HASH --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=10 --endpoint-url http://localhost:8000

"""
