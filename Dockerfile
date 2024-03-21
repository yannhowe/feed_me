FROM python:3.9.19-alpine

COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
ENTRYPOINT ["python"]
CMD ["feed_me.py"]