from flask import Flask, session, request
from flask_session import Session
import boto3
from boto3.dynamodb.conditions import Key
import requests

app = Flask(__name__)

app.secret_key = 'x>JE6fdsYR.ssJzC7pw'
SESSION_TYPE = 'filesystem'
app.config.from_object(__name__)
Session(app)
db = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")
ratingTable = db.Table('rateIt')

def putItem(table, item):
    table.put_item(Item=item)

def getItem(table, key, value):
    #query item which url=value from table
    response = table.query(KeyConditionExpression=Key(key).eq(value))
    return response['Items'][0]

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
        userinfo = requests.get("https://www.googleapis.com/oauth2/v1/userinfo", params={"alt": "json", "access_token": token})
        print(userinfo.json())
        session['logged_in'] = True
        print(session['logged_in'])
    return "login"
    

@app.route("/get/rating")
def getRating():
    url = request.args.get('url')
    rating = getItem(ratingTable, 'url', url)
    return rating

@app.route("/post/rating", methods=['POST'])
def postLike():
    content = request.json
    loggedIn = session.get('logged_in')
    print(loggedIn)
    return "foo"





if __name__ == "__main__":
    app.run(debug=True)
"""
aws dynamodb create-table --table-name rateIt --attribute-definitions AttributeName=url,AttributeType=S --key-schema AttributeName=url,KeyType=HASH --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=10 --endpoint-url http://localhost:8000
aws dynamodb put-item --table-name rateIt --item '{"url": {"S": "http://www.google.com"}, "likes": {"N": "10"}, "dislikes": {"N": "2"}}' --endpoint-url http://localhost:8000
"""