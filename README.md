# Discord bot that will run a music quiz

## Installation

`pip install -r requirements.txt`

## Running

Fill out `.env` with the fields and create `config.json` with your spotify api credentials.

`python bot.py`

## Spotify To Youtube

Modification of [this](https://github.com/saulojoab/Spotify-To-Youtube)

Usage `python spotifyToYoutube.py <spotify playlist> [filename]`

## How to play

Start the quiz with `?start-quiz`. This will start playing some songs. Guessing the correct artist is 1 point, guessing the correct title is 1 point, and if you guess both correctly then you will get a bonus point at the end of the round.

### Bot Commands

`?load-playlist <spotify playlist url> <genre>` - Will load a spotify playlist into songs/ and reload the bot's song cache to reflect this change

`?start-quiz <genre>` - Will start the quiz based on the songs loaded from songs/

`!pass` - Will pass the current song if the `(num_players/2)+1` condition is met

`?genres` - Creates an embed to list all of the loaded genres
