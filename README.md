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

### Docker Compose
```
git clone https://github.com/yannhowe/feed_me.git
docker-compose up
```
Use: Use [postman](https://www.getpostman.com/) and the [provided collection](https://github.com/yannhowe/feed_me/blob/master/feed-me.postman_collection.json)

### Using pipenv
- Clone repository
- install [pipenv](https://pipenv.readthedocs.io/en/latest/)
- Run: ```pipenv run flask run```
- Test: ```pipenv run pytest```
- Use: Use [postman](https://www.getpostman.com/) and the [provided collection](https://github.com/yannhowe/feed_me/blob/master/feed-me.postman_collection.json)