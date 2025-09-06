import discord
from discord.ext import commands
from discord import app_commands
import logging
import os
import aiohttp
from yt_dlp import YoutubeDL
import asyncio

YDL_OPTS = {"format": "bestaudio/best", "noplaylist": True}
FFMPEG_OPTS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn"
}
ytdl = YoutubeDL(YDL_OPTS)


class Client(commands.Bot):
    async def on_ready(self):
        print(f"Logged on as {self.user}")
        try:
            guild=discord.Object(id=1412900647304691815)
            synced= await self.tree.sync(guild=guild)
            print(f"Synced {len(synced)} commands to guild {guild.id}") 
        except Exception as e:
            print(f"Error in syncing commands:{e} ")

    async def on_message(self,message):
        if message.author==self.user:
            return
        if message.content.startswith('hello'):
            await message.channel.send(f"Hi there {message.author}")
intents=discord.Intents.default()
intents.message_content=True

client=Client(command_prefix='!',intents=intents)

GUILD_ID=discord.Object(id=1412900647304691815)

@client.tree.command(name='helloo',description='Say hello!',guild=GUILD_ID)
async def sayHello(interaction=discord.Interaction):
    await interaction.response.send_message("Hi there")

@client.tree.command(name='printer',description='I will print whatever u give me',guild=GUILD_ID)
async def printer(interaction:discord.Interaction, printer: str):
    await interaction.response.send_message(printer)

@client.tree.command(name='embed',description='Embed demo',guild=GUILD_ID)
async def Embed(interaction:discord.Interaction):
    embed=discord.Embed(title='I am a Title',url='https://www.youtube.com/shorts/K4b-ODV2MKM',description='I am a description',color=discord.Color.red())
    embed.set_thumbnail(url='https://www.shyamh.com/images/blog/music.jpg')
    embed.add_field(name='Field 1',value='Song Name',inline=False)
    embed.add_field(name='Field 2',value='Song Name')
    embed.set_footer(text='This is the footer')    
    embed.set_author(name='Karthik Shankar',url='https://www.youtube.com/@kaarthik_shankar/featured',icon_url='https://m.media-amazon.com/images/M/MV5BM2QzYzc3MDMtZDgyOC00NjdkLTkzN2UtNmE1MTVkMjgyNTY3XkEyXkFqcGc@._V1_.jpg')
    await interaction.response.send_message(embed=embed)

class View(discord.ui.View):
    @discord.ui.button(label='Click me!',style=discord.ButtonStyle.red,emoji='🔥')
    async def button_callback(seld,button,interaction):
        await button.response.send_message("You have clicked the button!")

@client.tree.command(name='button',description='Displaying a button',guild=GUILD_ID)
async def myButton(interaction=discord.Interaction):
    await interaction.response.send_message(view=View())

class Menu(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(
                label='Option 1',
                description='This is option 1',
                emoji='🔥'
            ),
            discord.SelectOption(
                label='Option 2',
                description='This is option 2',
                emoji='😂'
            ),
            discord.SelectOption(
                label='Option 3',
                description='This is option 3',
                emoji='👻'
            )       
        ]
        super().__init__(placeholder='Please choose an option:',min_values=1,max_values=1,options=options)
    async def callback(self,interaction:discord.Interaction):
        await interaction.response.send_message(f"Yayy you picked {self.values[0]}")
    

class MenuView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(Menu())

@client.tree.command(name='menu',description='Displaying a drop down menu',guild=GUILD_ID)
async def myMenu(interaction=discord.Interaction):
    await interaction.response.send_message(view=MenuView())

@client.tree.command(name="join", description="Bot joins your voice channel", guild=GUILD_ID)
async def join(interaction: discord.Interaction):
    
    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.response.send_message("❌ You need to be in a voice channel first.")
        return

    channel = interaction.user.voice.channel
    vc = interaction.guild.voice_client  

    if vc is None:
        await channel.connect()
        await interaction.response.send_message(f"✅ Joined **{channel.name}**")
    else:
        if vc.channel.id != channel.id:
            await vc.move_to(channel)
            await interaction.response.send_message(f"🔁 Moved to **{channel.name}**")
        else:
            await interaction.response.send_message("ℹ️ I'm already in your voice channel.")



@client.tree.command(name="play_from_a_url", description="Play audio from a YouTube URL", guild=GUILD_ID)
async def play(interaction: discord.Interaction, url: str):
    await interaction.response.defer()  

    vc = interaction.guild.voice_client
    if vc is None:
        await interaction.followup.send("❌ I'm not in a voice channel. Use `/join` first.")
        return

    loop = asyncio.get_running_loop()
    try:
        info = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
    except Exception as e:
        await interaction.followup.send(f"❌ Failed to extract audio: `{e}`")
        return

    stream_url = info.get("url")
    title = info.get("title", "Unknown title")

    if vc.is_playing():
        vc.stop()


    source = discord.FFmpegPCMAudio(stream_url, **FFMPEG_OPTS)
    vc.play(source, after=lambda e: print(f"player finished: {e}" if e else "player finished"))

    await interaction.followup.send(f"🎶 Now playing: **{title}**")


@client.tree.command(name="leave", description="Disconnect from voice", guild=GUILD_ID)
async def leave(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc is None:
        await interaction.response.send_message("❌ I'm not connected to a voice channel.")
        return
    await vc.disconnect()
    await interaction.response.send_message("👋 Disconnected.")

@client.tree.command(name="lyrics", description="Fetch song lyrics", guild=GUILD_ID)
async def lyrics(interaction: discord.Interaction, song: str, artist: str):
    await interaction.response.defer()

    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.lyrics.ovh/v1/{artist}/{song}"  
            async with session.get(url) as resp:
                print("STATUS:", resp.status)  
                text = await resp.text()
                print("RESPONSE:", text)

                if resp.status != 200:
                    await interaction.followup.send("❌ Could not fetch lyrics.")
                    return

                data = await resp.json()

        embed = discord.Embed(
            title=f"{song} - {artist}",
            description=data.get("lyrics", "No lyrics found"),
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"⚠️ Error: {e}")
        print("Error in /lyrics:", e)

@client.tree.command(name="track", description="Get detailed track info", guild=GUILD_ID)
async def track(interaction: discord.Interaction, song: str, artist: str):
    await interaction.response.defer()

    url = f"https://musicbrainz.org/ws/2/recording/?query=recording:{song}%20AND%20artist:{artist}&fmt=json"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={"User-Agent": "LyricLoungeBot/1.0 ( https://yourprojecturl.com )"}) as resp:
                if resp.status != 200:
                    await interaction.followup.send("❌ Could not fetch track info.")
                    return

                data = await resp.json()

        if not data.get("recordings"):
            await interaction.followup.send("📭 No results found.")
            return

        track_data = data["recordings"][0]  

        
        title = track_data.get("title", "Unknown")
        artist_name = track_data["artist-credit"][0]["name"]
        album = track_data["releases"][0]["title"] if "releases" in track_data else "Unknown"
        length = track_data.get("length", 0) // 1000 if "length" in track_data else None

        embed = discord.Embed(title=f"{title} - {artist_name}", color=discord.Color.green())
        embed.add_field(name="Album", value=album, inline=False)
        if length:
            embed.add_field(name="Duration", value=f"{length // 60}:{length % 60:02d}", inline=False)

        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"⚠️ Error: {e}")
        print("Error in /track:", e)

playlists = {}  

@client.tree.command(name="playlist", description="Manage your personal playlist", guild=GUILD_ID)
@app_commands.describe(action="add/remove/view/clear", song="Song name if adding or removing")
async def playlist(interaction: discord.Interaction, action: str, song: str = None):
    user_id = interaction.user.id
    if user_id not in playlists:
        playlists[user_id] = []

    if action == "add" and song:
        playlists[user_id].append(song)
        await interaction.response.send_message(f"✅ Added **{song}** to your playlist.")
    elif action == "remove" and song:
        try:
            playlists[user_id].remove(song)
            await interaction.response.send_message(f"🗑️ Removed **{song}**.")
        except ValueError:
            await interaction.response.send_message("❌ Song not found in playlist.")
    elif action == "view":
        if playlists[user_id]:
            songs = "\n".join(playlists[user_id])
            await interaction.response.send_message(f"🎶 Your playlist:\n{songs}")
        else:
            await interaction.response.send_message("📭 Your playlist is empty.")
    elif action == "clear":
        playlists[user_id].clear()
        await interaction.response.send_message("🧹 Cleared your playlist.")
    else:
        await interaction.response.send_message("❌ Invalid action or missing song.")

@client.tree.command(name="help", description="Show all available commands", guild=GUILD_ID)
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎵 Lyric Lounge - Help Menu",
        description="Here are the commands you can use:",
        color=discord.Color.purple()
    )
    embed.add_field(
        name="📝 /lyrics <song> - <artist>",
        value="Fetch and display song lyrics instantly.",
        inline=False
    )

    embed.add_field(
        name="🎶 /playlist [add/remove/view/clear] [song]",
        value="Manage your personal playlist easily.",
        inline=False
    )
    embed.add_field(
        name="🥡 /description <song> - <artist>",
        value="Fetch the song descripton",
        inline=False
    )
    embed.add_field(
        name=" 🔗  /url <youtube url>",
        value="Plays the song from the youtube url ",
        inline=False
    )
    embed.add_field(
        name=" 🖇️  /join",
        value="Joins the audio channel",
        inline=False
    )    
    
    embed.add_field(
        name="👋 /leave",
        value="Disconnect the bot from the voice channel.",
        inline=False
    )
    embed.add_field(
        name="ℹ️ /help",
        value="Show this help menu.",
        inline=False
    )

    embed.set_footer(text="Lyric_Lounge | Your music companion 🎧")

    await interaction.response.send_message(embed=embed)





client.run('MTQxMjg1MzQzNjIzNTM4MzA0NA.Gz3mDj.4UybNxvUJC0S7KNEWxzNS1eiyw_YpKpgxNShNw')























