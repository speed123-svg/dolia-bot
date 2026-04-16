import asyncio
import os

import discord
import wavelink
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

LAVALINK_URI = os.getenv("LAVALINK_URI", "http://localhost:2333")
_node_connected = False
_music_loaded = False
_commands_synced = False

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(
    command_prefix="d!",
    intents=intents,
    help_command=None,
    description="Dolia — Song-Weaver of the Scarlet Kingdom",
)


@bot.event
async def on_ready():
    print(f"[Dolia] Logged in as {bot.user}")
    node = wavelink.Node(
        uri=LAVALINK_URI,
        password=os.getenv("LAVALINK_PASSWORD"),
    )
    await wavelink.Pool.connect(nodes=[node], client=bot)
    print("[Dolia] Lavalink connected ✓")
    await bot.load_extension("music")
    print("[Dolia] Music cog loaded ✓")
    await bot.tree.sync()
    print("[Dolia] Slash commands synced ✓")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name="the melody between worlds 🎶",
        )
    )
    print("[Dolia] Ready ✨")


async def main():
    async with bot:
        await bot.start(os.getenv("DISCORD_TOKEN"))


asyncio.run(main())
