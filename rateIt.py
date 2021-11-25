from flask import Flask, session, request
from flask_session import Session
import boto3
from boto3.dynamodb.conditions import Key


app = Flask(__name__)

app.secret_key = 'x>JE6YR.ssJzC7pw'
SESSION_TYPE = 'mongoDb'
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

@app.route('/login')
def login():
    session['logged_in'] = True

@app.route("/get/rating")
def getRating():
    url = request.args.get('url')
    rating = getItem(ratingTable, 'url', url)
    return rating

@app.route("/post/rating")
def postLike():
    url = request.args.get('url')
    loggedIn = session.get('logged_in')






"""
aws dynamodb create-table --table-name rateIt --attribute-definitions AttributeName=url,AttributeType=S --key-schema AttributeName=url,KeyType=HASH --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=10 --endpoint-url http://localhost:8000
aws dynamodb put-item --table-name rateIt --item '{"url": {"S": "http://www.google.com"}, "likes": {"N": "10"}, "dislikes": {"N": "2"}}' --endpoint-url http://localhost:8000
"""