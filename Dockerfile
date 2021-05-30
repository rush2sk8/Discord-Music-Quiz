FROM node

WORKDIR /app

COPY bot.py .
COPY config.json .
COPY ./songs/ ./songs/
COPY ./spotifyToYoutube.py .
COPY ./requirements.txt .

RUN apt-get update -y && apt-get install python3-pip -y

RUN pip3 install -r requirements.txt

RUN npm install -g pm2
