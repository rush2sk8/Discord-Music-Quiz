FROM node

WORKDIR /app

COPY bot.py .
COPY ./songs/ ./songs/
COPY ./spotifyToYoutube.py .
COPY ./requirements.txt .

RUN apt-get update -y && apt-get install python3-pip -y

RUN pip3 install -r requirements.txt

RUN npm install -g pm2

ENTRYPOINT pm2 start bot.py --update-env --name music_quiz --interpreter python3 && pm2 logs -f
