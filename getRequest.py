from flask import Flask, request, session
import rateIt
import db

empty = {'likes': 0, 'dislikes': 0, 'userRating': 0}


@db.app.route("/get/rating")
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
