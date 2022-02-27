import boto3
from boto3.dynamodb.conditions import Key
import uuid
from flask import Flask, request, session
from graphql import Undefined

db = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")
ratingTable = db.Table('rateIt')
userTable = db.Table('users')


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
def getUsername(userId):
    try:
        user = queryItem(userTable, 'userId', userId)
        return user['username']
    except:
        return False

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



def appendComment(url, comment):
    if checkUser(comment["userId"]):
        comment["id"] = str(uuid.uuid4())
        comment["answers"] = []
        comments=queryItem(ratingTable, 'url', url)
        if not comments:
            putItem(ratingTable, {"url": url, "likes": 0, "dislikes": 0, "comments": []})
        elif "comments" not in comments.keys():
            ratingTable.update_item(Key={'url': url}, UpdateExpression="set comments = :val", ExpressionAttributeValues={':val': [comment]})
        ratingTable.update_item(Key={'url': url}, UpdateExpression="Set comments = list_append(comments, :val)", ExpressionAttributeValues={':val': [comment]})
    else:
        return False

def checkComment(url, commentId):
    try: 
        if queryItem(ratingTable, 'url', url):
            for comment in queryItem(ratingTable, 'url', url)["comments"]:
                if comment["id"] == commentId:
                    return True
    except:
        return False
    return False

def appendAnswer(url, commentId, answer):
    if checkUser(answer["userId"]):
        if not checkComment(url, commentId):
            return False
        answer["id"] = str(uuid.uuid4())
        comments = ratingTable.query(KeyConditionExpression=Key('url').eq(url))["Items"][0]["comments"]
        for comment in comments:
            if comment["id"] == commentId:
                comment["answers"].append(answer)
                
        ratingTable.update_item(Key={'url': url}, UpdateExpression="set comments = :val", ExpressionAttributeValues={':val': comments})


def getComments(url, indexFrom, indexTo):
    try:
        comments = ratingTable.query(KeyConditionExpression=Key('url').eq(url))["Items"][0]["comments"][indexFrom:indexTo]
        for comment in comments:
            comment["username"] = getUsername(comment["userId"])
        return comments
    except:
        return []
