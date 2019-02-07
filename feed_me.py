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

user_follow_user = db.Table("user_follow_user",
    db.Column("follower_id", db.Integer, db.ForeignKey("users.id")),
    db.Column("followee_id", db.Integer, db.ForeignKey("users.id"))
)

#Base = declarative_base()
#
#user_follow_user = Table("user_follow_user", Base.metadata,
#    Column("follower_id", Integer, ForeignKey("users.id"), primary_key=True),
#    Column("followee_id", Integer, ForeignKey("users.id"), primary_key=True)
#)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))
    followees = db.relationship("User",
                    secondary=user_follow_user,
                    primaryjoin=id==user_follow_user.c.follower_id,
                    secondaryjoin=id==user_follow_user.c.followee_id,
                    backref=db.backref("followers", lazy='joined'), lazy='dynamic')

    def __init__(self, username, followees):
        self.username = username
        self.followees = followees

class UserSchema(ma.Schema):
    class Meta:
        # Fields to expose
        fields = ('id', 'username', 'followees')

user_schema = UserSchema()
users_schema = UserSchema(many=True)


#class Follower(db.Model):
#    id = db.Column(db.Integer, primary_key=True)
#    follower_id = db.Column(db.Integer)
#    followee_id = db.Column(db.Integer, db.Foreignkey('user.id'))
#    follower = db.relationship('User', backref = 'followees')
#
#    def __init__(self, follower_id, followee_id):
#        self.follower_id = follower_id
#        self.followee_id = followee_id

#class FollowerSchema(ma.Schema):
#    class Meta:
#        # Fields to expose
#        fields = ('follower_id', 'followee_id')
#        
#follower_schema = FollowerSchema()
#followers_schema = FollowerSchema(many=True)


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

# endpoint to show all follows
@app.route("/follow", methods=["GET"])
def get_follows():
    all_follows = User.query.all()
    result = UserSchema.dump(all_follows)
    return jsonify(result.data)

# endpoint to create new activity
@app.route("/activity", methods=["POST"])
def add_activity():
    actor = request.json['actor']
    verb = request.json['verb']
    object = request.json['object']
    target = request.json['target']

    # Checks - https://techspot.zzzeek.org/2008/09/09/selecting-booleans/
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
    
    if request.json['follow']:
        username = request.json['follow']
        return jsonify({"error": "no key named \'follow\'" })

    if not username:
        jsonify({"error": "user to follow not specified" })
    
    (username_exists, ), = db.session.query(exists().where(User.username==username))

    if  username_exists:
        user_feed = Activity.query.filter_by(actor=username).all()
        result = { "my_feed": activities_schema.dump(user_feed).data}
        return jsonify(result)
    else:
        return jsonify({"error": "no user named %s" % username })
