from flask import Flask, session, request
from flask_session import Session
import boto3
from boto3.dynamodb.conditions import Key
import requests
import uuid

from requests.api import put

app = Flask(__name__)

app.secret_key = 'x>JE6fdsYR.ssJzC7pw'
SESSION_TYPE = 'filesystem'
app.config.from_object(__name__)
Session(app)
db = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")
ratingTable = db.Table('rateIt')
userTable = db.Table('users')

def putItem(table, item):
    table.put_item(Item=item)

def incrementLikes(url, number, userId):
    #increment likes for url
    updateItem(ratingTable, 'url', url, 'ADD likes : ' + str(number))
    #add url to liked urls for user
    updateItem(ratingTable, 'userId', userId, 'ADD likedUrls : "' + url + '"') 
def incrementDisLikes(url, number, userId):
    #increment dislikes for url
    updateItem(ratingTable, 'url', url, 'ADD dislikes : ' + str(number))
    #add url to disliked urls for user
    updateItem(ratingTable, 'userId', userId, 'ADD dislikedUrls : "' + url + '"')

def updateItem(table, key, value, update):
    #update item in db
    table.update_item(Key={key: value}, UpdateExpression=update)

def queryItem(table, key, value):
    #query item which url=value from table
    try:
        response = table.query(KeyConditionExpression=Key(key).eq(value))
    except:
        return False
    return response['Items'][0]

def scanItem(table, key, value):
    #scan table for item with key=value
    try:
        response = table.scan(FilterExpression=Key(key).eq(value))
    except:
        return False
    return response['Items'][0]

def createUser(googleUserId, username):
    #create new user in db
    uuid_string = str(uuid.uuid4())
    session["userId"]=uuid_string
    putItem(userTable, {'googleUserId': googleUserId, 'username': username, 'userId': uuid_string})

def checkGoogleUser(googleUserId):
    #check if user exists in db
    user = scanItem(userTable, 'googleUserId', googleUserId)
    if not user:
        return False
    else:
        return True
def checkUser(uuid_string):
    #check if user exists in db
    user = queryItem(userTable, 'userId', uuid_string)
    if user:
        return True
    else:
        return False


def verifyOauth(accessToken):
    #verify if access token is valid
    response = requests.get("https://www.googleapis.com/oauth2/v1/tokeninfo", params={"access_token": accessToken})
    if response.status_code == 200:
        return True
    else:
        return False


@app.route('/login', methods=['POST'])
def login():
    token = request.json["token"]
    validToken = verifyOauth(token)
    if validToken:
        userinfo = requests.get("https://www.googleapis.com/oauth2/v1/userinfo", params={"alt": "json", "access_token": token}).json()
        id = userinfo["id"]
        if checkGoogleUser(id):
            session["logged_in"]=True
            session["userId"]=scanItem(userTable, 'googleUserId', id)["userId"]
            return "login"
        else: 
            createUser(id, userinfo["given_name"])
            session["logged_in"]=True
            session["userId"]=scanItem(userTable, 'googleUserId', id)["userId"]
            return "login"
    else:
        return "invalid token"
    

@app.route("/get/rating")
def getRating():
    url = request.args.get('url')
    rating = queryItem(ratingTable, 'url', url)
    return rating

@app.route("/post/rating", methods=['POST'])
def postRating():
    content = request.json
    if session["logged_in"] and checkUser(session["userId"]):
        url = content["url"]
        if content["rating"]==1:
            if scanItem(ratingTable, 'url', url)["dislikes"]!=None:
                incrementDisLikes(url, -11, session["userId"])
            incrementLikes(url, 1, session["userId"])
        elif content["rating"]==-1:
            if scanItem(ratingTable, 'url', url)["likes"]!=None:
                incrementLikes(url, -1, session["userId"])
            incrementDisLikes(url, 1, session["userId"])
        elif content["rating"]==0:
            if scanItem(ratingTable, 'url', url)["likes"]!=None:
                incrementLikes(url, -1, session["userId"])
            if scanItem(ratingTable, 'url', url)["dislikes"]!=None:
                incrementDisLikes(url, -1, session["userId"])

        return "success"
    else:
        return "not logged in"





if __name__ == "__main__":
    app.run(debug=True)
"""
aws dynamodb create-table --table-name rateIt --attribute-definitions AttributeName=url,AttributeType=S --key-schema AttributeName=url,KeyType=HASH --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=10 --endpoint-url http://localhost:8000
aws dynamodb put-item --table-name rateIt --item '{"url": {"S": "http://www.google.com"}, "likes": {"N": "10"}, "dislikes": {"N": "2"}}' --endpoint-url http://localhost:8000

aws dynamodb create-table --table-name users --attribute-definitions AttributeName=userId,AttributeType=S AttributeName=googleUserId,AttributeType=S --key-schema AttributeName=userId,KeyType=HASH AttributeName=googleUserId,KeyType=RANGE --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=10 --endpoint-url http://localhost:8000

"""