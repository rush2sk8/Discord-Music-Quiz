import asyncio
import json
import os
import random
import re
import subprocess
from pathlib import Path

import discord
from threading import Lock
import youtube_dl
from discord.ext import commands
from dotenv import load_dotenv
from fuzzywuzzy import fuzz

load_dotenv(dotenv_path=Path('.')/'.env')

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
NUM_SONGS_PER_ROUND = int(os.getenv('NUM_SONGS_PER_ROUND'))
QUIZ_CHANNEL_NAME = os.getenv('QUIZ_CHANNEL_NAME')

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='?', intents=intents)

youtube_dl.utils.bug_reports_message = lambda: ''

title_mutex = Lock()
artist_mutex = Lock()
round_mutex = Lock()


ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    # bind to ipv4 since ipv6 addresses cause issues sometimes
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'options': '-vn -ss 40',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class Song():

    def __init__(self, title, artist, url):
        self.title = title
        self.artist = artist
        self.url = url

    def __str__(self):
        return f'{self.title} : {self.artist}'


all_songs = {
    "all": []
}

songs = []

curr_song = {
    "song": None,
    "live": False,
    "artist_correct": False,
    "title_correct": False,
    "filename": None,
    "index": 0,
    "player_artist_correct": None,
    "player_title_correct": None,
    "pass": 0
}

players = {}


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


def get_random_song():
    ''' Return a random song and remove it from the list so no duplicates '''
    random.seed(random.randint(0, 1000000))
    song = random.choice(songs)
    songs.remove(song)
    return song


async def load_songs_cache(message):
    ''' Loads the songs into the songs map '''
    idx = 0
    # Go through all the files in ./songs/
    for file in os.listdir(os.path.join(os.getcwd(), 'songs')):

        # Get only json files
        if file.endswith(".json"):

            # Open the file
            with open(f'songs/{file}', 'r') as sf:
                songs_dict = json.load(sf)

                # Get the genre from the filename
                genre = file.split("-_-")[-1].replace(".json", '').lower()

                # if we havent loaded the genre in the dict then create it
                if genre not in all_songs:
                    all_songs[genre] = []

                # Iterate songs in this file
                for s in songs_dict:
                    # Strip unecessary parts of the artist and title
                    t = s["title"].split("-")[0].strip().split("(")[0].strip()
                    a = s['artist'].split(',')[0].strip()

                    if t == '' or a == '':
                        continue

                    # create song object
                    song = Song(title=t,
                                artist=a, url=s["url"])

                    # add the song to all the songs and the current genre
                    all_songs['all'].append(song)
                    all_songs[genre].append(song)

                    print(song)
                    idx += 1

    # Print out how many songs were loaded
    print(idx)


async def stop_playing(message):
    ''' Stops any currently playing audio '''
    vc = message.guild.voice_client

    try:
        if vc:
            vc.stop()
        else:
            await message.author.voice.channel.connect()
    except:
        pass


def restart_game():
    ''' Restarts the game by clearing the state variables'''

    curr_song["song"] = None
    curr_song["live"] = False
    curr_song["artist_correct"] = False
    curr_song["title_correct"] = False
    curr_song["filename"] = None
    curr_song["index"] = 0
    curr_song["pass"] = 0
    curr_song["player_artist_correct"] = None
    curr_song["player_title_correct"] = None
    players.clear()
    songs.clear()


async def next_song(message):
    ''' Skip to the next song and change the state of the game accordingly'''
    # Only print out a leaderboard after the first question
    if curr_song["index"] != 0:
        await create_leaderboard_embed(message)

    # Set some variables
    curr_song["song"] = get_random_song()
    curr_song["artist_correct"] = False
    curr_song["pass"] = 0
    curr_song["title_correct"] = False
    curr_song["index"] += 1
    curr_song["player_artist_correct"] = None,
    curr_song["player_title_correct"] = None

    # Stop playing music
    await stop_playing(message)
    vc = message.guild.voice_client

    try:
        # Get and store the ytdl source filename
        filename = await YTDLSource.from_url(curr_song["song"].url, loop=bot.loop, stream=True)
        curr_song["filename"] = filename

        # Print answers so I can cheat from console xD
        print(curr_song["song"].artist)
        print(curr_song["song"].title)

        # Play the song
        vc.play(filename)

    except:
        # If an error occurs then skip to the next song
        await next_song(message)

        # Decrement current song index because a song wasn't played
        curr_song["index"] -= 1


async def load_playlist(message, url, genre):
    ''' Loads a playlist and reloads the new songs into our cache '''

    # Create cool loading embed
    embed = discord.Embed(title="Loading Playlist...",
                          description='Please wait until we finish importing your playlist')
    embed.set_thumbnail(
        url="https://mir-s3-cdn-cf.behance.net/project_modules/disp/04de2e31234507.564a1d23645bf.gif")

    # Send loading message
    loading = await message.channel.send(embed=embed)

    # Create subprocess and wait for it to finish
    output = subprocess.call(
        ['python', 'spotifyToYoutube.py', url, genre], shell=True)

    # Delete the message once loading is done
    await loading.delete()

    # Reload all the songs
    await load_songs_cache(None)

    # Tell them how many songs were loaded
    await message.channel.send(f'Loaded {output} songs!')


@bot.event
async def on_ready():
    """Event when the bot logs in"""

    # Load songs
    await load_songs_cache(None)

    # Plug me
    await bot.change_presence(activity=discord.Streaming(name="by rush2sk8", url='https://www.twitch.tv/rush2sk8'))
    print('We have logged in as {0.user}'.format(bot))


async def check_round_number(message):
    ''' Checks the current round and decides to skip the song or to end the game'''

    # Acquire the mutex
    if round_mutex.acquire(False):
        # If we are still playing then get the next song
        if curr_song["index"] < NUM_SONGS_PER_ROUND:
            await next_song(message)
        else:
            # Otherwise we have won stop music
            await stop_playing(message)
            await create_final_leaderboard(message)
            restart_game()
        round_mutex.release()


@bot.event
async def on_message(message):
    ''' Event for messages. Facilitates the game '''

    # If the message is from the bot ignore it
    if message.author.id == bot.user.id:
        return

    # If we are in bot spam (for now)
    if message.channel.name == QUIZ_CHANNEL_NAME:
        m = message.content

        # Only react to users that are in a voice channel
        if message.author.voice:

            # If the current game is live then facilitate it
            if curr_song["live"]:

                # Gather all the users in the voice channel and make them players
                for user in message.author.voice.channel.members:
                    if user not in players and (user.id != bot.user.id) and user.bot == False:
                        players[user] = 0

                # If they pass the song then count the pass and move on
                if m == "!pass" or m == "!p":
                    curr_song["pass"] += 1

                    # Calculate max players for a pass: (num_players/2) + 1
                    max_players_for_pass = (len(players)//2)+1

                    await message.channel.send(f"⏩ `{min(curr_song['pass'], max_players_for_pass)}/{max_players_for_pass} votes to pass the song.`")

                    # If the pass is successful then move on to forwarding the round
                    if curr_song["pass"] >= max_players_for_pass:
                        await check_round_number(message)

                # If they didn't pass
                else:
                    # See if they got something right
                    got_right = False

                    # Check if their answer was correct for the artist if its not already been answered
                    if not curr_song["artist_correct"]:

                        # If 85% of the string is similar to the answer then award them the win for that
                        if fuzz.ratio(m.lower(), curr_song["song"].artist.lower()) >= 85:

                            # Get the artist mutex and fail fast if its in use
                            if artist_mutex.acquire(False):

                                # Mark the message as correct
                                await message.add_reaction("✅")

                                # Increment their score
                                players[message.author] += 1

                                # Mark the artist as being correct
                                curr_song["artist_correct"] = True

                                # Store the current player who got this right (to calculate if they get a bonus point)
                                curr_song["player_artist_correct"] = message.author

                                # Tell them that they were right
                                await message.channel.send(f'{message.author.mention} Correct! You earn **1pt**')
                                got_right = True
                                artist_mutex.release()

                    # Check if their answer was correct for the title  if its not already been answered
                    if not curr_song["title_correct"]:

                        # If 85% of the string is similar to the answer then award them the win for that
                        if fuzz.ratio(m.lower(), curr_song["song"].title.lower()) >= 85:

                            # Get the title mutex and fail fast if its in use
                            if title_mutex.acquire(False):

                                # Mark the message as correct
                                await message.add_reaction("✅")

                                # Increment their score
                                players[message.author] += 1

                                # Mark the title as being correct
                                curr_song["title_correct"] = True

                                # Store the current player who got this right (to calculate if they get a bonus point)
                                curr_song["player_title_correct"] = message.author

                                # Tell them that they were right
                                await message.channel.send(f'{message.author.mention} Correct! You earn **1pt**')
                                got_right = True
                                title_mutex.release()

                    # If they got nothing wrong mark it as wrong
                    if not got_right:
                        await message.add_reaction("❌")

                # If both the title and artist have been correctly guessed
                if curr_song["title_correct"] and curr_song["artist_correct"]:

                    # If the same player guessed the title and artist correctly give them an extra point
                    if curr_song["player_title_correct"] == curr_song["player_artist_correct"]:
                        players[curr_song["player_title_correct"]] += 1

                    # Forward the round
                    await check_round_number(message)

            # If the command is start quiz
            elif m.startswith("?start-quiz"):
                split = m.split(" ")

                # If they dont have the correct
                if len(split) != 2:
                    return await create_genres_embed(message)

                # Get the last element as the genre
                genre = split[-1].lower()

                # if the genere they specify doesnt exist
                if genre not in all_songs.keys():
                    return await message.channel.send(f'{genre.capitalize()} is not a valid genre!')

                # Add all the songs into the songs list
                for song in all_songs[genre]:
                    songs.append(song)

                print(f'Curr List: {len(songs)}')

                # Get the current voice channel of the person who started the game
                vc = message.author.voice.channel
                voice = discord.utils.get(
                    bot.voice_clients, guild=message.guild)

                # Only join vc if you aren't already in
                if voice == None:
                    await vc.connect()

                # Mark the game as live
                curr_song["live"] = True

                # Start the game
                await check_round_number(message)

            # If the command is load playlist
            elif m.startswith("?load-playlist"):
                split = m.split(" ")

                # If the number of arguments is incorrect then yell
                if len(split) != 3:
                    return await message.channel.send("Usage: `?load-playlist <spotify playlist> <genre>`")

                # Get the url
                url = split[1]

                genre = split[-1]

                # Make the regex and search
                res = re.search(
                    r"^http(s)?:\/\/open.spotify.com\/playlist\/.*$", url)

                # If the search was a match then go ahead and load it
                if res:
                    await load_playlist(message, url, genre)
                else:
                    # Otherwise tell them the url is invalid
                    return await message.channel.send(
                        "Spotify playlist url not valid. Please match the following: `^http(s)?:\/\/open.spotify.com\/playlist\/.*$`")

            # If they run the generes command
            elif m == "?genres":
                await create_genres_embed(message)


def add_users_to_embed(embed):
    ''' Adds all of the users to the embed '''

    # Sort users by their score
    players_sorted = dict(
        sorted(players.items(), key=lambda item: item[1], reverse=True))

    users = ""

    for i, (player, score) in enumerate(players_sorted.items()):

        # Add cool stuff for place 1-3
        if i == 0:
            users += f'🥇- {player.mention} - {score} pts\n\n'
        elif i == 1:
            users += f'🥈- {player.mention} - {score} pts\n\n'
        elif i == 2:
            users += f'🥉- {player.mention} - {score} pts\n\n'
        else:
            users += f'{player.mention} - {score} pts\n\n'

    embed.add_field(value=users, name='\u200b', inline=False)


async def create_genres_embed(message):
    ''' Creates and sends the embed for all the available genres'''
    embed = discord.Embed(
        title="Available Genres", description="Usage: ?start-quiz [genre]", color=0x001eff)
    embed.set_footer(text="?genres")

    genres = ""
    for i, genre in enumerate(all_songs.keys()):
        genres += f'{i+1}. {genre.capitalize()}\n'

    embed.add_field(
        value=genres, name="Please Choose from one of the following genres (by name):", inline=False)

    await message.channel.send(embed=embed)


async def create_leaderboard_embed(message):
    ''' Creates and sends the embed for the leaderboard '''
    embed = discord.Embed(title=f"It was: {curr_song['song'].artist} - {curr_song['song'].title}",
                          description="__**LeaderBoard**__", color=0xff0000, url=curr_song['song'].url)
    embed.set_thumbnail(
        url=curr_song["filename"].data['thumbnails'][0]['url'])

    add_users_to_embed(embed=embed)

    embed.set_footer(
        text=f"Music Quiz - Track {curr_song['index']}/{NUM_SONGS_PER_ROUND}")
    await message.channel.send(embed=embed)


async def create_final_leaderboard(message):
    ''' Creates and sends the embed for all final leaderboard'''

    # Show the last song with the leaderboad
    await create_leaderboard_embed(message)

    # create the final leaderboard embed
    embed = discord.Embed(title=f"Music Quiz Ranking",
                          description="", color=0xf6a623)

    add_users_to_embed(embed=embed)

    # Show the final leaderboard
    await message.channel.send(embed=embed)

    # If in a voice channel then leave
    if message.guild.voice_client:
        await message.guild.voice_client.disconnect()

# Run the bot
bot.run(DISCORD_TOKEN)
