# Discord Music Quiz Bot

[![Deploy bot](https://github.com/rushadantia/Discord-Music-Quiz/actions/workflows/main.yml/badge.svg?branch=master)](https://github.com/rushadantia/Discord-Music-Quiz/actions/workflows/main.yml) ![Docker Pulls](https://img.shields.io/docker/pulls/rush2sk8/discord-music-quiz) ![Docker Stars](https://img.shields.io/docker/stars/rush2sk8/discord-music-quiz) 

Are you the type of person who like flexing their musical knowledge? Then music bot is for you! This bot will join your voice channel and play a selection of music that you have personally loaded in. `?start-quiz` and away you go. Keep in mind that the bot doesn't come with any music preloaded and that you will need to load playlists of your own into the bot. 

**NOTE: This bot only works in 1 discord server at a time. SUPPORT FOR MULTIPLE GUILDS IS NOT SUPPORTED AT THIS TIME**

## Installation

`pip install -r requirements.txt`

## Running

Fill out `.env` with the fields defined in `example.env`

`python bot.py`

## Spotify To Youtube

Modification of [this](https://github.com/saulojoab/Spotify-To-Youtube)

Usage `python spotifyToYoutube.py <spotify playlist> [filename]`


## Docker 
`docker-compose build`

`docker-compose up`

**OR**
https://hub.docker.com/r/rush2sk8/discord-music-quiz

`docker pull rush2sk8/discord-music-quiz:latest:latest`

You need to supply the image with the following environment variables:

* `DISCORD_TOKEN` - Your own discord [developer](https://discord.com/developers/applications) bot token 
* `NUM_SONGS_PER_ROUND`- An integer representing the number of songs per game
* `QUIZ_CHANNEL_NAME`- The name of the channel to play in. i.e music-quiz
* `SPOTIFY_CLIENT_ID` - Client ID for your [Spotify Developer](https://developer.spotify.com/documentation/web-api/) account
* `SPOTIFY_CLIENT_SECRET` - Client ID for your [Spotify Developer](https://developer.spotify.com/documentation/web-api/) account

Run with the following command

```
docker run -d -e DISCORD_TOKEN='' \
     -e NUM_SONGS_PER_ROUND=10 \
     -e QUIZ_CHANNEL_NAME='music-quiz' \
     -e SPOTIFY_CLIENT_ID='' \
     -e SPOTIFY_CLIENT_SECRET='' \
rush2sk8/discord-music-quiz:latest
```

## How to play

You can only interact with the bot while sitting in a voice channel. Running any of the following commands will not work if you are not in VC.

`?start-quiz <genre>` - This will start playing some songs for the given genre. Guessing the correct artist is 1 point, guessing the correct title is 1 point, and if you guess both correctly then you will get a bonus point at the end of the round.

`?load-playlist <spotify playlist URL> <genre>` - This command can only be run while the quiz is inactive and will block any other interaction with the bot while it loads the playlist. Will load a Spotify playlist into the bot's memory and will be tagged with the genre that you provide. If you have multiple playlists to load that share the same genre these will be compounded into a single category. For example if 2 players load a playlist with the genre "Rap" then when you list the available genres then there will be a singular "Rap" genre. 

`?genres` - This command will display a list of all of the currently loaded playlists (genres)

`!pass` - When the music quiz is live this will allow you and others to vote to pass the song. **NOTE: The song will continue playing till the end so if you don't know the song then just !pass**



