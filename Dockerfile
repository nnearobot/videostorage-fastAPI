FROM python:3.11

RUN pip3 install --no-cache-dir pipenv

RUN mkdir /videostorage_api
WORKDIR /videostorage_api

COPY . .

RUN pipenv install --system --deploy

RUN chmod a+x /videostorage_api/start.sh
