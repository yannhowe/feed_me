from flask import Flask, request, jsonify
from sqlalchemy import exists, Integer, ForeignKey,  Column, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from datetime import datetime
import os
import json

app = Flask(__name__) 
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'feed_me.sqlite')
db = SQLAlchemy(app)
ma = Marshmallow(app)

#####
# DB Models
#####

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))

    def __init__(self, username):
        self.username = username

class UserSchema(ma.Schema):
    class Meta:
        # Fields to expose
        fields = ('id', 'username')

user_schema = UserSchema()
users_schema = UserSchema(many=True)


class Following(db.Model):
    __tablename__ = 'following'
    follower = db.Column("follower", db.String(80), db.ForeignKey("users.username"), primary_key=True)
    followee = db.Column("followee", db.String(80), db.ForeignKey("users.username"), primary_key=True)

    def __init__(self, follower, followee):
        self.follower = follower
        self.followee = followee

class FollowingSchema(ma.Schema):
    class Meta:
        # Fields to expose
        fields = ('follower', 'followee')

following_schema = FollowingSchema()
followings_schema = FollowingSchema(many=True)


class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    actor = db.Column(db.String(80), db.ForeignKey('users.id'), nullable=False)
    verb = db.Column(db.String(80), nullable=False)
    object = db.Column(db.String(80))
    target = db.Column(db.String(80), db.ForeignKey('users.id'), nullable=False)
    datetime = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, actor, verb, object, target):
        self.actor = actor
        self.verb = verb
        self.object = object
        self.target = target

class ActivitySchema(ma.Schema):
    class Meta:
        fields = ('actor', 'verb', 'object', 'target', 'datetime')
        dateformat = ('%Y-%m-%dT%H:%M:%S')

activity_schema = ActivitySchema()
activities_schema = ActivitySchema(many=True)


#####
# Endpoints
#####

# See if server running
@app.route("/")
def hello():
    return "Hello World!"

# endpoint to reset database
@app.route("/reset", methods=["GET"])
def setup():
    db.drop_all()
    db.create_all()
    users_to_create=["ivan", "niko", "eric"]
    activity_to_create=[   
        {"actor":"ivan", "verb": "share", "object":"post:1", "target":"eric"}, 
        {"actor":"niko", "verb": "like", "object":"post:2", "target":"ivan"}, 
        {"actor":"eric", "verb": "post", "object":"post:3", "target":""}, 
        {"actor":"ivan", "verb": "follow", "object":"null", "target":"niko"}
        ]
    followings_to_create=[
        {"followee": "eric", "follower": "ivan"}
        ]
    for user in users_to_create:
        new_user = User(user)
        db.session.add(new_user)
    for activity in activity_to_create:
        new_activity = Activity(activity["actor"], activity["verb"], activity["object"], activity["target"])
        db.session.add(new_activity)
    for following in followings_to_create:
        new_following = Following(following["follower"], following["followee"])
        db.session.add(new_following)
    db.session.commit()    
    all_users = User.query.all()
    all_activity = Activity.query.all()
    all_following = Following.query.all()
    result = {"users": users_schema.dump(all_users).data, "Activities": activities_schema.dump(all_activity).data, "Followings": followings_schema.dump(all_following).data}
    return jsonify(result)

# endpoint to show all users
@app.route("/user", methods=["GET"])
def get_user():

    try:
        all_users = User.query.all()
    except:
        return jsonify({"error": "no users" })
    
    result = users_schema.dump(all_users)
    return jsonify(result.data)

# endpoint to show all activities
@app.route("/activity", methods=["GET"])
def get_activity():

    try:
        all_activity = Activity.query.all()
    except:
        return jsonify({"error": "no activity" })

    result = activities_schema.dump(all_activity)
    return jsonify(result.data)

# endpoint to create new activity
@app.route("/activity", methods=["POST"])
def add_activity():
    
    try:
        actor = request.json['actor']
        verb = request.json['verb']
        object = request.json['object']
        target = request.json['target']
    except:
        return jsonify({"error": "something wrong with JSON request" })

    try:
        # Checks - https://techspot.zzzeek.org/2008/09/09/selecting-booleans/
        (actor_exists, ), = db.session.query(exists().where(User.username==actor))
        (target_exists, ), = db.session.query(exists().where(User.username==target))
    except:
        return jsonify({"error": "Either actor or target doesn't exist in database"})

    if not verb:
        return jsonify({"error": "empty verb" })

    if actor_exists:
        if  target_exists:
            new_activity = Activity(actor, verb, object, target)
            db.session.add(new_activity)
            db.session.commit()
            return activity_schema.jsonify(new_activity)
        else:
            return jsonify({"error": "no target named %s" % target })
    else:
            return jsonify({"error": "no actor named %s" % actor })

# endpoint to show user feed
@app.route("/feed/<username>", methods=["GET"])
def get_user_feed(username):
    results_per_page = 1

    try:
        page = int(request.args.get('page', 1))    
    except:
        abort(404)

    try:
        (username_exists, ), = db.session.query(exists().where(User.username==username))
    except:
        return jsonify({"error": "no user named %s" % username })

    if  username_exists:
        user_feed = Activity.query.filter_by(actor=username).paginate(page, results_per_page, False)
        
        # pagination stuff
        next_page = page + 1
        previous_page = page-1
        if previous_page<1:
            previous_page = 1
        
        if user_feed.has_next:
            next_url = request.base_url + "?" + "page=" + str(next_page)
        if user_feed.has_prev:
            previous_url = request.base_url + "?" + "page=" + str(previous_page)

        if user_feed.has_next and user_feed.has_prev:
            result = { "my_feed": activities_schema.dump(user_feed.items).data, "next_url": next_url, "previous_url": previous_url }
        elif user_feed.has_next:
            result = { "my_feed": activities_schema.dump(user_feed.items).data, "next_url": next_url }
        elif user_feed.has_prev:
            result = { "my_feed": activities_schema.dump(user_feed.items).data, "previous_url": previous_url }
        else:
            result = { "my_feed": activities_schema.dump(user_feed.items).data }

        return jsonify(result)
    else:
        return jsonify({"error": "no user named %s" % username })

# endpoint to show user's friends feed
@app.route("/feed/<username>/friends", methods=["GET"])
def get_user_friends_feed(username):
    results_per_page = 1

    try:
        page = int(request.args.get('page', 1))    
    except:
        abort(404)

    try:
        (username_exists, ), = db.session.query(exists().where(User.username==username))
    except:
        return jsonify({"error": "no user named %s" % username })

    if  username_exists:
        user_follows_list = db.session.query(Following.followee).filter_by(follower=username).all()

        if not user_follows_list:
            return jsonify({"error": "user \'%s\' doesn't follow anyone" % username })

        user_follows_list = [r.followee for r in user_follows_list]
        user_friends_feed = Activity.query.filter(Activity.actor.in_(user_follows_list)).paginate(page, results_per_page, False)
        
        # pagination stuff
        next_page = page + 1
        previous_page = page-1
        if previous_page<1:
            previous_page = 1
        
        if user_friends_feed.has_next:
            next_url = request.base_url + "?" + "page=" + str(next_page)
        if user_friends_feed.has_prev:
            previous_url = request.base_url + "?" + "page=" + str(previous_page)

        if user_friends_feed.has_next and user_friends_feed.has_prev:
            result = { "friends_feed": activities_schema.dump(user_friends_feed.items).data, "next_url": next_url, "previous_url": previous_url }
        elif user_friends_feed.has_next:
            result = { "friends_feed": activities_schema.dump(user_friends_feed.items).data, "next_url": next_url }
        elif user_friends_feed.has_prev:
            result = { "friends_feed": activities_schema.dump(user_friends_feed.items).data, "previous_url": previous_url }
        else:
            result = { "friends_feed": activities_schema.dump(user_friends_feed.items).data}
        return jsonify(result)

    else:
        return jsonify({"error": "no user named %s" % username })

# endpoint to show all follows
@app.route("/follows", methods=["GET"])
def get_follows():

    try:
        all_follows = Following.query.all()
    except:
        return jsonify({"error": "no follows" })

    if all_follows:
        result = followings_schema.dump(all_follows)
        return jsonify(result)
    else:
        return jsonify({"error": "no follows"})

# endpoint to follow user feed
@app.route("/feed/<username>", methods=["POST"])
def follow_user_feed(username):
    
    try:
        jsonData = request.json
    except:
        return jsonify({"error": "something wrong with JSON request" })
    
    if 'follow' in jsonData:
        followee = jsonData['follow']
        if username == followee:
            return jsonify({"error": "user cannot follow himself" })
        action = 'follow'

    if 'unfollow' in jsonData:
        followee = jsonData['unfollow']
        action = 'unfollow'

    if not followee:
        return jsonify({"error": "user to follow not specified" })

    try:  
        (user_exists, ), = db.session.query(exists().where(User.username==username))
        (followee_exists, ), = db.session.query(exists().where(User.username==followee))
        following_to_check = db.session.query(Following).filter(Following.follower==username, Following.followee==followee)
        following_exists = db.session.query(following_to_check.exists()).scalar()
    except:
        return jsonify({"error": "Error for %s following %s, can't find one of them in the database." % (username, followee) })
        
    if user_exists and followee_exists:
        if action is "follow":

            if not following_exists:
                following = Following(username, followee)
                db.session.add(following)
                db.session.commit()    
                result = { "follow": following_schema.dump(following).data }
                return jsonify(result)
            else:
                return jsonify({"error": "%s already follows %s" % (username, followee) })
                
        if action is "unfollow":

            if following_exists:
                following = Following.query.filter_by(follower=username).filter_by(followee=followee).first()
                db.session.delete(following)
                db.session.commit()    
                result = { "unfollow": following_schema.dump(following).data }
                return jsonify(result)
            else:
                return jsonify({"error": "cannot unfollow, no such follow exists" })

        return jsonify({"error": "Somethin broke, cannot follow or unfollow" })
        
    else:
        if not followee_exists:
            return jsonify({"error": "no user named %s" % followee })
        if not user_exists:
            return jsonify({"error": "no user named %s" % username })

if __name__ == '__main__':
    app.run(host='0.0.0.0')