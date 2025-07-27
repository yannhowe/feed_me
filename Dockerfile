FROM python:3.14.0rc1-alpine

COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
ENTRYPOINT ["python"]
CMD ["feed_me.py"]