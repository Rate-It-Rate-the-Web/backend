from flask import Flask, request, session

import requests


app = Flask(__name__)

app.secret_key = 'dev'
SESSION_TYPE = 'filesystem'
app.config.from_object(__name__)


def verifyOauth(accessToken):
    # verify if access token is valid
    response = requests.get(
        "https://www.googleapis.com/oauth2/v1/tokeninfo", params={"access_token": accessToken})
    if response.status_code == 200:
        return True
    else:
        return False


if __name__ == "__main__":
    app.run()
"""
sudo dynamodb

aws dynamodb create-table --table-name rateIt --attribute-definitions AttributeName=url,AttributeType=S --key-schema AttributeName=url,KeyType=HASH --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=10 --endpoint-url http://localhost:8000

aws dynamodb create-table --table-name users --attribute-definitions AttributeName=userId,AttributeType=S --key-schema AttributeName=userId,KeyType=HASH --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=10 --endpoint-url http://localhost:8000

"""
