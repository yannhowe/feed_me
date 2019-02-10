# feed-me
feed-me is a social media activity feed.

## Stuff Used
- pipenv 2018.11.26: To manage python dependencies
- Python 3.7
- Flask: Python Framework
- Tavern[pytest]: Testing 
- flask_sqlalchemy
- flask_marshmallow
- marshmallow-sqlalchemy
- docker/docker-compose


## Quick Start

Using Docker Compose:
```
git clone https://github.com/yannhowe/feed_me.git
cd feed_me
docker-compose up
```
Using pipenv ([install it](https://pipenv.readthedocs.io/en/latest/)):
```
git clone https://github.com/yannhowe/feed_me.git
cd feed_me
pipenv install
pipenv run flask run
pipenv run pytest
```

Use [postman](https://www.getpostman.com/) and import the [provided collection](https://github.com/yannhowe/feed_me/blob/master/feed-me.postman_collection.json) to query the API


## End Points

The different end points allow you to carry out the following tasks
1. build an activity feed
1. read your own activity feed that contains my activities posted
1. follow a friend's activity feed
1. retrieve a feed of all activities of friends that I follow
1. unfollow a friend's activity feed

Task | URL | Method | URL Params | Data Params | Success Response | Error Response |
-----|----|--------|------------|-------------|------------------|----------------|
1 | /activity | `POST` | none | ```{"actor": "eric", "verb": "punched", "object": "null", "target": "niko" }``` | ```{"actor": "eric", "datetime": "2019-02-08T08:07:19", "object": "null", "target": "niko", "verb": "punched"}``` | ```{"error": "something wrong with JSON request" }```
2 | /feed/:username | `GET` | **Required:** username=[string] | none | `{"my_feed": [{ "actor": "ivan" "datetime": "2019-02-08T08:07:13", "object": "post:1", "target": "eric", "verb": "share" }]}` | `{"follow":{"followee":"ivan","follower":"eric"}}` | `{ "error": "" }`
3 | /feed/:username | `POST` | **Required:** username=[string] | `"follow": username` | `{"follow":{"followee":"ivan","follower":"eric"}}` | `{ "error": "" }`
4 | /feed/:username/friends | `GET` | **Required:** username=[string] | none | `{"friends_feed": [{"actor": "eric", "datetime": "2019-02-08T08:11:23", "object": "post:3", "target": "","verb": "post"}]}` | `{ "error": "" }`
5 | /feed/:username | `POST` | **Required:** username=[string] | `"unfollow":username` | `{"unfollow":{"followee":"ivan","follower":"eric"}}` | `{ "error": "" }`


## Database Schema

### Users

Field | Type | Description
------|------|---------------
id | INTEGER NOT NULL | PRIMARY KEY (id)
username | VARCHAR(80)

Defined in the code [here](https://github.com/yannhowe/feed_me/blob/master/feed_me.py#L21)

### Following

Defined in the code [here](https://github.com/yannhowe/feed_me/blob/master/feed_me.py#L38)

Field | Type | Description
------|------|---------------        
follower | VARCHAR(80) NOT NULL | FOREIGN KEY(follower) REFERENCES users (username), PRIMARY KEY (follower, followee)
followee | VARCHAR(80) NOT NULL | FOREIGN KEY(followee) REFERENCES users (username), PRIMARY KEY (follower, followee)


### Activity
Defined  in the code [here](https://github.com/yannhowe/feed_me/blob/master/feed_me.py#L56)

Field | Type | Description
------|------|---------------
id | INTEGER NOT NULL | PRIMARY KEY
actor | VARCHAR(80) NOT NULL | FOREIGN KEY(actor) REFERENCES users (id),
verb | VARCHAR(80) NOT NULL
object | VARCHAR(80)
target | VARCHAR(80) NOT NULL | FOREIGN KEY(target) REFERENCES users (id)
datetime | DATETIME


## Going Further

There are a number of things for the project I would change if this went into production at any scale:
- Structure project files by  model/endpoint/functionality/project team
- Use a database sutable for the scale like AWS RDS Aurora serverless
- Use IDs as a unique constraint instead of usernames directly
- Hide all the endpoints created for development convenience

## Growing in Scale and Features

![image](./Web%20App%20Reference%20Architecture%20(4).png)
***Fig. 1** Overall Architecture. Might differ slightly based on design choices.*

Thoughts on scaling and adding features to the APIs for customer happiness:
- Don't use flask to run the API, package and run the app with a WSGI application server like [Gunicorn](https://gunicorn.org/)
- Use an API gateway like [KONG](https://konghq.com/kong/)/[APIGEE](https://apigee.com/api-management/#/homepage).[Amazon API Gateway](https://aws.amazon.com/api-gateway/) for
    - Visibility: Monitor API usage and behaviour
    - Manage/deploy/deprecate/conduct AB testing on different versions of the API
    - Security
    - Flexibility to redeploy and migrate backends as required to other SaaS, serverless etc.
- Reducing load - Good read from Stripe [here](https://stripe.com/blog/rate-limiters)
    - Load shedding for less important read queries, client should retry
    - Load limiting for users, Implement API Key usage
- Load test to find single instance API max rate ([flood.io](https://flood.io/))
- Use caching like [Memcached](https://memcached.org/) with [Flask-Cache](https://flask-caching.readthedocs.io/en/latest/) to cache data so reads don't hit the relational database
- Start thinking about migrating away from flask/whatever ORM you are using to something lighter (could make development complex)
- Start thinking about how you want to scale the application instances vertically/horizontally in AWS/Kubernetes (could cost a lot of money)
- Use databases as a service (like [AWS RDS Aurora Serverless](https://aws.amazon.com/rds/aurora/serverless/)) to start quick, small and cheap. It scales to 64TB and 200,000 writes/s at the [largest instance](https://aws.amazon.com/rds/mysql/instance-types/) (db.m4.16xlarge)
- Once it reaches a scale where cost/performance is a problem consider shifting to self-provisioned/configured databases because you probably understand the problem now well enough to optimize it correctly for cost/performance

The above should be more than enough for servicing 1,000,000 users and shouldn't be too much of an issue for a Relational Database with caching, rate limiting, horizontally scaling app cluster for a simple text API like this one. 

If we expand the API to upload images and other media as well as
- Decouple image/object processing services from HTTP end points using queing ([SQS](https://aws.amazon.com/sqs/), [RabbitMQ](https://www.rabbitmq.com/)) and notifications ([SNS](https://aws.amazon.com/sns/)) to fan out
- Backend tasks like processing images, videos can be done using serverless functions ([Lambda](https://aws.amazon.com/lambda/), [kubeless](https://kubeless.io/))
- You probably don't need streaming ([Kinesis](https://aws.amazon.com/kinesis/), [Kaftka](https://kafka.apache.org/)) unless you need to replay requests or have multiple consumers and really big data streams made of small bits
- Use object storage to store objects ([AWS S3](https://aws.amazon.com/s3/), [b2](https://www.backblaze.com/b2/cloud-storage.html), [minio](https://www.minio.io/)), basically infinitely scalable storage
- Use CDN ([AWS Cloudfront](https://aws.amazon.com/cloudfront/)/[Akamai](https://www.akamai.com/)/[varnish](https://varnish-cache.org/)) to serve objects/static content with low latency

Possible Stack (AWS Flavoured)
- DNS: [Route 53](https://aws.amazon.com/route53/)
- CDN: [AWS Cloudfront](https://aws.amazon.com/cloudfront/)
- Load Balancing: [ELB](https://aws.amazon.com/elasticloadbalancing/) / [Amazon API Gateway](https://aws.amazon.com/api-gateway/)
- Compute: [EC2](https://aws.amazon.com/ec2/)/[EKS](https://aws.amazon.com/eks/)/[ECS](https://aws.amazon.com/ecs/)/[Lambda](https://aws.amazon.com/lambda/)
- Database: [RDS Aurora Serverless](https://aws.amazon.com/rds/aurora/serverless/)
- Caching: [Elasticache](https://aws.amazon.com/elasticache/)
- Storage: [AWS S3](https://aws.amazon.com/s3/)
- CI/CD: [Codestar](https://aws.amazon.com/codestar/)

Other things that probably need to be thought about beyond the API:
- Backup? (Dumping DB to S3)
- Cross AZ/Region deployment for disaster recovery
- Monitoring (CloudWatch/API Gateway)
- CI/CD? (AWS Codestar/gitlab)
