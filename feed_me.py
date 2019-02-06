from flask import Flask, request, jsonify
from sqlalchemy import exists
from sqlalchemy.ext.declarative import declarative_base
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


class Follower(db.Model):
    __tablename__ = 'followers'
    follower_id = db.Column(db.Integer, db.Foreignkey('users.id'))
    followee_id = db.Column(db.Integer, db.Foreignkey('users.id'))
    follower = db.relationship('User', foreign_keys="follower_id", backref = 'followees')


class FollowerSchema(ma.Schema):
    class Meta:
        # Fields to expose
        fields = ('follower_id', 'followee_id')
        
follower_schema = FollowerSchema()
followers_schema = FollowerSchema(many=True)


class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    actor = db.Column(db.String(80), db.ForeignKey('user.id'), nullable=False)
    verb = db.Column(db.String(80), nullable=False)
    object = db.Column(db.String(80))
    target = db.Column(db.String(80), db.ForeignKey('user.id'), nullable=False)
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
    for user in users_to_create:
        new_user = User(user)
        db.session.add(new_user)
    for activity in activity_to_create:
        print(activity)
        new_activity = Activity(activity["actor"], activity["verb"], activity["object"], activity["target"])
        db.session.add(new_activity)
    db.session.commit()    
    all_users = User.query.all()
    all_activity = Activity.query.all()
    result = {"users": users_schema.dump(all_users).data, "Activities": activities_schema.dump(all_activity).data}
    return jsonify(result)

# endpoint to show all users
@app.route("/user", methods=["GET"])
def get_user():
    all_users = User.query.all()
    result = users_schema.dump(all_users)
    return jsonify(result.data)

# endpoint to show all activities
@app.route("/activity", methods=["GET"])
def get_activity():
    all_activity = Activity.query.all()
    result = activities_schema.dump(all_activity)
    return jsonify(result.data)

# endpoint to create new activity
@app.route("/activity", methods=["POST"])
def add_activity():
    actor = request.json['actor']
    verb = request.json['verb']
    object = request.json['object']
    target = request.json['target']

    # Checks https://techspot.zzzeek.org/2008/09/09/selecting-booleans/
    (actor_exists, ), = db.session.query(exists().where(User.username==actor))
    (target_exists, ), = db.session.query(exists().where(User.username==target))

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
    
    (username_exists, ), = db.session.query(exists().where(User.username==username))

    if  username_exists:
        user_feed = Activity.query.filter_by(actor=username).all()
        result = { "my_feed": activities_schema.dump(user_feed).data}
        return jsonify(result)
    else:
        return jsonify({"error": "no user named %s" % username })

# endpoint to follow user feed
@app.route("/feed/<username>/", methods=["POST"])
def follow_user_feed(username):

    follow = request.json['follow']

    if not follow:
        jsonify({"error": "no user to follow" })
    
    (username_exists, ), = db.session.query(exists().where(User.username==username))

    if  username_exists:
        user_feed = Activity.query.filter_by(actor=username).all()
        result = { "my_feed": activities_schema.dump(user_feed).data}
        return jsonify(result)
    else:
        return jsonify({"error": "no user named %s" % username })
