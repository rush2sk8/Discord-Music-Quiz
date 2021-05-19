import asyncio
import logging
import os
import random
from pathlib import Path

import discord
import youtube_dl
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path('.')/'.env')
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
bot = commands.Bot(command_prefix='?', intents=discord.Intents.default())

youtube_dl.utils.bug_reports_message = lambda: ''


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
    'options': '-vn -ss 40'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class Song():

    def __init__(self, title, artist, url):
        self.title = title
        self.artist = artist
        self.url = url

    def __str__(self):
        return f'{self.title} {self.artist}'


songs = [
    Song(url="https://youtu.be/6UQ-M6nLfLI?t=48",
         artist="Brotherman Bill", title="Terrible Tim"),
    Song(url="https://www.youtube.com/watch?v=AcMUULoT_jk",
         artist="Ted Gardestad", title="Satelit"),
    Song(url="https://www.youtube.com/watch?v=eynnYLXW3Fo",
         artist="Victor Wootton", title="Isn't she lovely"),
    Song(url="https://www.youtube.com/watch?v=4cn_woPvjQI",
         title="Black Betty", artist="Ram Jam"),
    Song(url="https://www.youtube.com/watch?v=h66dI0q_9As",
         title="Take Me Out", artist="Franz Ferdinand"),
    Song(url="https://www.youtube.com/watch?v=r78xfXZb_WU",
         title="Electric Feel", artist="MGMT"),
    Song(url="https://www.youtube.com/watch?v=DtrIWQ8J9jw",
         title="In Da Club", artist="50 cent"),
    Song(url="https://www.youtube.com/watch?v=8ay_BkRuv-o",
         title="All Star", artist="Smash Mouth"),
    Song(url="https://www.youtube.com/watch?v=PuoyrrZfC9o",
         title="Time of our lives", artist="Pitbull, Ne-Yo")
]

curr_song = {
    "song": None,
    "live": False
}


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
    song = random.choice(songs)
    songs.remove(song)
    return song


async def play_song(message):
    curr_song["song"] = get_random_song()

    server = message.guild
    vc = server.voice_client

    try:
        vc.stop()
    except:
        pass

    try:
        filename = await YTDLSource.from_url(curr_song["song"].url, loop=bot.loop, stream=True)
        print(curr_song["song"])
        vc.play(filename)
    except:
        pass


@bot.event
async def on_ready():
    """Event when the bot logs in"""
    await bot.change_presence(activity=discord.Streaming(name="by rush2sk8", url='https://www.twitch.tv/rush2sk8'))
    print('We have logged in as {0.user}'.format(bot))


async def wait_15_for_song():

    await asyncio.sleep(15)


@bot.event
async def on_message(message):
    if message.author.id == bot.user.id:
        return

    if message.channel.id == 574639555802824726:
        m = message.content
        print(m)

        if curr_song["live"]:
            if m.lower() == curr_song["song"].artist.lower() or \
                    m.lower() == curr_song["song"].title.lower():
                await message.channel.send(f"{message.author.mention} Correct")
                await play_song(message)

        elif m == "?start-quiz":
            curr_song["live"] = True
            await message.author.voice.channel.connect()
            await play_song(message)
            print("before")
            await asyncio.sleep(5)
            print("after")

bot.run(DISCORD_TOKEN)
