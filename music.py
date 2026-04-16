import random
from urllib.parse import urlparse

import discord
import wavelink
from discord import app_commands
from discord.ext import commands

from embeds import control_panel_embed, error_embed, help_embed, loop_mode_label, queue_embed, search_embed, status_embed
from responses import (
    IDLE_LINES,
    LOOP_OFF_LINES,
    LOOP_QUEUE_LINES,
    LOOP_TRACK_LINES,
    NOT_IN_VC_LINES,
    NOT_PLAYING_LINES,
    NO_TRACK_LINES,
    PAUSE_LINES,
    PLAY_LINES,
    QUEUE_LINES,
    RESUME_LINES,
    SEARCH_LINES,
    SKIP_LINES,
    STOP_LINES,
    QUEUE_ENDED_LINES,
    TRACK_END_LINES,
    TRACK_ERROR_LINES,
    VOLUME_LINES,
    say,
)


def user_in_vc(interaction):
    return interaction.user.voice is not None


def is_url(query):
    parsed = urlparse(query)
    return bool(parsed.scheme and parsed.netloc)


async def get_player(interaction):
    if interaction.guild.voice_client:
        return interaction.guild.voice_client

    channel = interaction.user.voice.channel
    return await channel.connect(cls=wavelink.Player, self_deaf=True)


class VolumeModal(discord.ui.Modal, title="Set Dolia's Volume"):
    volume = discord.ui.TextInput(
        label="Volume (0-100)",
        placeholder="50",
        min_length=1,
        max_length=3,
    )

    def __init__(self, cog):
        super().__init__(timeout=180)
        self.cog = cog

    async def on_submit(self, interaction):
        player = self.cog.get_guild_player(interaction.guild)
        if not player:
            return await interaction.response.send_message(
                embed=error_embed(say(NOT_PLAYING_LINES)),
                ephemeral=True,
            )

        try:
            level = int(str(self.volume))
        except ValueError:
            return await interaction.response.send_message(
                embed=error_embed("✨ Dolia needs a whole number between 0 and 100."),
                ephemeral=True,
            )

        if not 0 <= level <= 100:
            return await interaction.response.send_message(
                embed=error_embed("✨ Dolia can only shape resonance between 0 and 100."),
                ephemeral=True,
            )

        await player.set_volume(level)
        await self.cog.refresh_panel(
            interaction.guild.id,
            note=f"{say(VOLUME_LINES)} Now set to **{level}%**.",
        )
        await interaction.response.send_message(
            embed=status_embed("Volume Shifted", f"Dolia now sings at **{level}%** volume."),
            ephemeral=True,
        )


class SearchResultSelect(discord.ui.Select):
    def __init__(self, cog, requester_id, tracks):
        self.cog = cog
        self.requester_id = requester_id
        self.tracks = tracks[:10]

        options = []
        for index, track in enumerate(self.tracks, start=1):
            options.append(
                discord.SelectOption(
                    label=f"{index}. {track.title}"[:100],
                    description=f"{track.author} | {track.length // 1000}s"[:100],
                    value=str(index - 1),
                )
            )

        super().__init__(
            placeholder="Choose the melody Dolia should weave...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction):
        if interaction.user.id != self.requester_id:
            return await interaction.response.send_message(
                embed=error_embed("🌊 Only the caller who summoned this search may choose from it."),
                ephemeral=True,
            )

        await interaction.response.defer()
        track = self.tracks[int(self.values[0])]
        status = await self.cog.enqueue_track(interaction, track)
        await interaction.edit_original_response(
            content=None,
            embed=status_embed(status["title"], status["description"]),
            view=None,
        )


class SearchResultsView(discord.ui.View):
    def __init__(self, cog, requester_id, tracks):
        super().__init__(timeout=120)
        self.add_item(SearchResultSelect(cog, requester_id, tracks))


class ControlPanelView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    async def ensure_player_access(self, interaction):
        player = self.cog.get_guild_player(interaction.guild)
        if not player or not player.current:
            await interaction.response.send_message(
                embed=error_embed(say(NOT_PLAYING_LINES)),
                ephemeral=True,
            )
            return None

        bot_channel = getattr(interaction.guild.me.voice, "channel", None)
        user_channel = getattr(interaction.user.voice, "channel", None)
        if bot_channel and user_channel and bot_channel != user_channel:
            await interaction.response.send_message(
                embed=error_embed("🌊 Dolia listens only to those standing in her current waters."),
                ephemeral=True,
            )
            return None

        return player

    @discord.ui.button(emoji="⏯️", style=discord.ButtonStyle.primary, custom_id="dolia:toggle")
    async def toggle(self, interaction, button):
        player = await self.ensure_player_access(interaction)
        if not player:
            return

        if player.paused:
            await player.pause(False)
            note = say(RESUME_LINES)
        else:
            await player.pause(True)
            note = say(PAUSE_LINES)

        await interaction.response.defer()
        await self.cog.refresh_panel(interaction.guild.id, note=note)

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.secondary, custom_id="dolia:skip")
    async def skip(self, interaction, button):
        player = await self.ensure_player_access(interaction)
        if not player:
            return

        await player.skip(force=True)
        await interaction.response.defer()
        await self.cog.refresh_panel(interaction.guild.id, note=say(SKIP_LINES))

    @discord.ui.button(emoji="⏹️", style=discord.ButtonStyle.danger, custom_id="dolia:stop")
    async def stop(self, interaction, button):
        player = await self.ensure_player_access(interaction)
        if not player:
            return

        player.queue.clear()
        await player.stop()
        await player.disconnect()
        await interaction.response.defer()
        await self.cog.refresh_panel(interaction.guild.id, note=say(STOP_LINES))

    @discord.ui.button(emoji="🔁", style=discord.ButtonStyle.secondary, custom_id="dolia:loop")
    async def loop(self, interaction, button):
        player = await self.ensure_player_access(interaction)
        if not player:
            return

        current_mode = player.queue.mode
        if current_mode == wavelink.QueueMode.normal:
            player.queue.mode = wavelink.QueueMode.loop
            note = say(LOOP_TRACK_LINES)
        elif current_mode == wavelink.QueueMode.loop:
            player.queue.mode = wavelink.QueueMode.loop_all
            note = say(LOOP_QUEUE_LINES)
        else:
            player.queue.mode = wavelink.QueueMode.normal
            note = say(LOOP_OFF_LINES)

        await interaction.response.defer()
        await self.cog.refresh_panel(interaction.guild.id, note=note)

    @discord.ui.button(emoji="🔊", style=discord.ButtonStyle.secondary, custom_id="dolia:volume")
    async def volume(self, interaction, button):
        player = self.cog.get_guild_player(interaction.guild)
        if not player or not player.current:
            return await interaction.response.send_message(
                embed=error_embed(say(NOT_PLAYING_LINES)),
                ephemeral=True,
            )

        await interaction.response.send_modal(VolumeModal(self.cog))


class ControlPanelView(discord.ui.View):
    def __init__(self, cog, player=None):
        super().__init__(timeout=None)
        self.cog = cog
        self.configure_controls(player)

    def configure_controls(self, player):
        paused = bool(player and getattr(player, "paused", False))
        current_loop = getattr(getattr(player, "queue", None), "mode", wavelink.QueueMode.normal)
        muted = bool(player and getattr(player, "volume", 100) == 0)

        self.toggle.label = "Resume" if paused else "Pause"
        self.toggle.emoji = "▶️" if paused else "⏸️"
        self.toggle.style = discord.ButtonStyle.success if paused else discord.ButtonStyle.primary

        if current_loop == wavelink.QueueMode.loop:
            self.loop.label = "Loop Track"
        elif current_loop == wavelink.QueueMode.loop_all:
            self.loop.label = "Loop Queue"
        else:
            self.loop.label = "Loop Off"

        self.mute.label = "Unmute" if muted else "Mute"
        self.mute.emoji = "🔊" if muted else "🔇"

    async def ensure_player_access(self, interaction):
        player = self.cog.get_guild_player(interaction.guild)
        if not player or not player.current:
            await interaction.response.send_message(
                embed=error_embed(say(NOT_PLAYING_LINES)),
                ephemeral=True,
            )
            return None

        bot_channel = getattr(interaction.guild.me.voice, "channel", None)
        user_channel = getattr(interaction.user.voice, "channel", None)
        if bot_channel and user_channel and bot_channel != user_channel:
            await interaction.response.send_message(
                embed=error_embed("Dolia listens only to those standing in her current waters."),
                ephemeral=True,
            )
            return None

        return player

    @discord.ui.button(label="Pause", emoji="⏸️", style=discord.ButtonStyle.primary, custom_id="dolia:toggle", row=0)
    async def toggle(self, interaction, button):
        player = await self.ensure_player_access(interaction)
        if not player:
            return

        if player.paused:
            await player.pause(False)
            note = say(RESUME_LINES)
        else:
            await player.pause(True)
            note = say(PAUSE_LINES)

        await interaction.response.defer()
        await self.cog.refresh_panel(interaction.guild.id, note=note)

    @discord.ui.button(label="Skip", emoji="⏭️", style=discord.ButtonStyle.secondary, custom_id="dolia:skip", row=0)
    async def skip(self, interaction, button):
        player = await self.ensure_player_access(interaction)
        if not player:
            return

        await player.skip(force=True)
        await interaction.response.defer()

    @discord.ui.button(label="Stop", emoji="⏹️", style=discord.ButtonStyle.danger, custom_id="dolia:stop", row=0)
    async def stop(self, interaction, button):
        player = await self.ensure_player_access(interaction)
        if not player:
            return

        player.queue.clear()
        await player.stop()
        await player.disconnect()
        await interaction.response.defer()
        await self.cog.refresh_panel(interaction.guild.id, note=say(STOP_LINES))

    @discord.ui.button(label="Loop Off", emoji="🔁", style=discord.ButtonStyle.secondary, custom_id="dolia:loop", row=0)
    async def loop(self, interaction, button):
        player = await self.ensure_player_access(interaction)
        if not player:
            return

        current_mode = player.queue.mode
        if current_mode == wavelink.QueueMode.normal:
            player.queue.mode = wavelink.QueueMode.loop
            note = say(LOOP_TRACK_LINES)
        elif current_mode == wavelink.QueueMode.loop:
            player.queue.mode = wavelink.QueueMode.loop_all
            note = say(LOOP_QUEUE_LINES)
        else:
            player.queue.mode = wavelink.QueueMode.normal
            note = say(LOOP_OFF_LINES)

        await interaction.response.defer()
        await self.cog.refresh_panel(interaction.guild.id, note=note)

    @discord.ui.button(label="Volume", emoji="🔊", style=discord.ButtonStyle.secondary, custom_id="dolia:volume", row=0)
    async def volume(self, interaction, button):
        player = await self.ensure_player_access(interaction)
        if not player:
            return

        await interaction.response.send_modal(VolumeModal(self.cog))

    @discord.ui.button(label="Queue", emoji="📜", style=discord.ButtonStyle.secondary, custom_id="dolia:queue", row=1)
    async def queue(self, interaction, button):
        player = await self.ensure_player_access(interaction)
        if not player:
            return

        await interaction.response.send_message(
            embed=queue_embed(list(player.queue), interaction.guild, player.current),
            ephemeral=True,
        )

    @discord.ui.button(label="Now Playing", emoji="💿", style=discord.ButtonStyle.secondary, custom_id="dolia:nowplaying", row=1)
    async def nowplaying(self, interaction, button):
        player = await self.ensure_player_access(interaction)
        if not player:
            return

        await interaction.response.send_message(
            embed=control_panel_embed(player, interaction.guild, note=say(PLAY_LINES)),
            ephemeral=True,
        )

    @discord.ui.button(label="Shuffle", emoji="🔀", style=discord.ButtonStyle.secondary, custom_id="dolia:shuffle", row=1)
    async def shuffle(self, interaction, button):
        player = await self.ensure_player_access(interaction)
        if not player:
            return

        queued_tracks = list(player.queue)
        if len(queued_tracks) < 2:
            return await interaction.response.send_message(
                embed=error_embed("Dolia needs at least two queued songs to shuffle the tide."),
                ephemeral=True,
            )

        random.shuffle(queued_tracks)
        player.queue.clear()
        for track in queued_tracks:
            player.queue.put(track)

        await interaction.response.defer()
        await self.cog.refresh_panel(
            interaction.guild.id,
            note="Dolia stirs the current and rearranges the waiting melodies.",
        )

    @discord.ui.button(label="Clear Queue", emoji="🧹", style=discord.ButtonStyle.secondary, custom_id="dolia:clear_queue", row=1)
    async def clear_queue(self, interaction, button):
        player = await self.ensure_player_access(interaction)
        if not player:
            return

        if not player.queue:
            return await interaction.response.send_message(
                embed=error_embed("Dolia's songbook is already clear."),
                ephemeral=True,
            )

        player.queue.clear()
        await interaction.response.defer()
        await self.cog.refresh_panel(
            interaction.guild.id,
            note="Dolia clears the waiting verses and leaves only the current melody.",
        )

    @discord.ui.button(label="Mute", emoji="🔇", style=discord.ButtonStyle.secondary, custom_id="dolia:mute", row=1)
    async def mute(self, interaction, button):
        player = await self.ensure_player_access(interaction)
        if not player:
            return

        current_volume = getattr(player, "volume", 100)
        if current_volume == 0:
            restore_volume = getattr(player, "_dolia_previous_volume", 100) or 100
            await player.set_volume(restore_volume)
            note = f"{say(VOLUME_LINES)} Restored to **{restore_volume}%**."
        else:
            player._dolia_previous_volume = current_volume
            await player.set_volume(0)
            note = "Dolia lowers the tide to a whispering silence."

        await interaction.response.defer()
        await self.cog.refresh_panel(interaction.guild.id, note=note)


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.panel_refs = {}

    def get_guild_player(self, guild):
        if not guild:
            return None
        return guild.voice_client

    def get_panel_view(self):
        return ControlPanelView(self)

    async def delete_panel(self, guild_id):
        message = await self.get_panel_message(guild_id)
        self.panel_refs.pop(guild_id, None)
        if not message:
            return

        try:
            await message.delete()
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            pass

    async def post_status_message(self, guild_id, title, description, *, channel=None):
        if channel is None:
            ref = self.panel_refs.get(guild_id)
            if ref:
                channel = self.bot.get_channel(ref["channel_id"])

        if channel is None:
            guild = self.bot.get_guild(guild_id)
            if guild and guild.system_channel:
                channel = guild.system_channel

        if channel is None:
            return None

        return await channel.send(embed=status_embed(title, description))

    async def get_panel_message(self, guild_id):
        data = self.panel_refs.get(guild_id)
        if not data:
            return None

        channel = self.bot.get_channel(data["channel_id"])
        if not channel:
            return None

        try:
            return await channel.fetch_message(data["message_id"])
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return None

    async def refresh_panel(self, guild_id, *, note=None, channel=None):
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return None

        player = self.get_guild_player(guild)
        if not player or not player.current:
            await self.delete_panel(guild_id)
            return None

        embed = control_panel_embed(player, guild, note=note or say(IDLE_LINES))
        view = ControlPanelView(self, player)

        message = await self.get_panel_message(guild_id)

        if channel is None:
            channel = message.channel if message else None
            if channel is None:
                ref = self.panel_refs.get(guild_id)
                if ref:
                    channel = self.bot.get_channel(ref["channel_id"])

        if channel is None:
            return None

        if message:
            try:
                await message.edit(embed=embed, view=view)
                self.panel_refs[guild_id] = {
                    "channel_id": message.channel.id,
                    "message_id": message.id,
                }
                return message
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                message = None

        new_message = await channel.send(embed=embed, view=view)
        self.panel_refs[guild_id] = {
            "channel_id": new_message.channel.id,
            "message_id": new_message.id,
        }
        return new_message

    async def enqueue_track(self, interaction, track):
        player = await get_player(interaction)
        print(
            f"[Dolia] enqueue_track guild={interaction.guild.id} "
            f"channel={getattr(getattr(player, 'channel', None), 'id', None)} "
            f"connected={getattr(player, 'connected', None)} current={bool(player.current)} "
            f"track={track.title}"
        )
        track.extras = {
            "requester_id": interaction.user.id,
            "requester_name": interaction.user.display_name,
        }

        if player.current:
            player.queue.put(track)
            position = len(list(player.queue))
            note = f"{say(QUEUE_LINES)} Added at **position {position}**."
            await self.refresh_panel(interaction.guild.id, note=note, channel=interaction.channel)
            return {
                "title": "Melody Queued",
                "description": f"**{track.title}** has been placed at **position {position}**.",
            }

        try:
            await player.play(track)
        except Exception as exc:
            print(f"[Dolia] player.play failed for guild={interaction.guild.id}: {exc!r}")
            raise

        print(f"[Dolia] player.play succeeded for guild={interaction.guild.id}: {track.title}")
        await self.refresh_panel(interaction.guild.id, note=say(PLAY_LINES), channel=interaction.channel)
        return {
            "title": "Melody Begun",
            "description": f"**{track.title}** is now flowing through Dolia's tide.",
        }

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload):
        player = payload.player
        if not player:
            return

        if player.queue:
            next_track = player.queue.get()
            await player.play(next_track)
            await self.refresh_panel(player.guild.id, note=say(PLAY_LINES))
        else:
            await self.delete_panel(player.guild.id)
            await self.post_status_message(
                player.guild.id,
                "The Tide Falls Silent",
                say(QUEUE_ENDED_LINES),
            )

    @commands.Cog.listener()
    async def on_wavelink_track_exception(self, payload):
        player = payload.player
        print(
            f"[Dolia] Track exception guild={getattr(getattr(player, 'guild', None), 'id', None)} "
            f"exception={getattr(payload, 'exception', None)!r}"
        )
        if player:
            await self.refresh_panel(player.guild.id, note=say(TRACK_ERROR_LINES))

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload):
        player = payload.player
        track = payload.track
        print(
            f"[Dolia] Track start guild={getattr(getattr(player, 'guild', None), 'id', None)} "
            f"track={getattr(track, 'title', None)}"
        )

    @commands.Cog.listener()
    async def on_wavelink_websocket_closed(self, payload):
        print(
            f"[Dolia] Websocket closed guild={payload.guild.id} "
            f"code={payload.code} by_discord={payload.by_discord} reason={payload.reason!r}"
        )

    @app_commands.command(name="play", description="Summon a melody by name or URL")
    @app_commands.describe(query="Song name or YouTube URL")
    async def play(self, interaction, query: str):
        if not user_in_vc(interaction):
            return await interaction.response.send_message(
                embed=error_embed(say(NOT_IN_VC_LINES)),
                ephemeral=True,
            )

        await interaction.response.defer(ephemeral=True)
        results = await wavelink.Playable.search(query, source=wavelink.TrackSource.YouTube)

        if hasattr(results, "tracks"):
            tracks = list(results.tracks)
        else:
            tracks = list(results)

        if not tracks:
            return await interaction.followup.send(
                embed=error_embed(say(NO_TRACK_LINES)),
                ephemeral=True,
            )

        if is_url(query):
            status = await self.enqueue_track(interaction, tracks[0])
            return await interaction.followup.send(
                embed=status_embed(status["title"], status["description"]),
                ephemeral=True,
            )

        view = SearchResultsView(self, interaction.user.id, tracks[:10])
        await interaction.followup.send(
            content=say(SEARCH_LINES),
            embed=search_embed(query, tracks[:10]),
            view=view,
            ephemeral=True,
        )

    @app_commands.command(name="stop", description="End the melody and depart")
    async def stop(self, interaction):
        player = self.get_guild_player(interaction.guild)
        if not player:
            return await interaction.response.send_message(
                embed=error_embed(say(NOT_PLAYING_LINES)),
                ephemeral=True,
            )

        player.queue.clear()
        await player.stop()
        await player.disconnect()
        await self.delete_panel(interaction.guild.id)
        await interaction.response.send_message(
            embed=status_embed("Waters Stilled", say(STOP_LINES)),
            ephemeral=True,
        )

    @app_commands.command(name="skip", description="Turn to the next verse")
    async def skip(self, interaction):
        player = self.get_guild_player(interaction.guild)
        if not player or not player.current:
            return await interaction.response.send_message(
                embed=error_embed(say(NOT_PLAYING_LINES)),
                ephemeral=True,
            )

        await player.skip(force=True)
        await self.refresh_panel(interaction.guild.id, note=say(SKIP_LINES))
        await interaction.response.send_message(
            embed=status_embed("Verse Skipped", say(SKIP_LINES)),
            ephemeral=True,
        )

    @app_commands.command(name="queue", description="View Dolia's songbook")
    async def queue(self, interaction):
        player = self.get_guild_player(interaction.guild)
        if not player:
            return await interaction.response.send_message(
                embed=error_embed(say(NOT_PLAYING_LINES)),
                ephemeral=True,
            )

        await interaction.response.send_message(
            embed=queue_embed(list(player.queue), interaction.guild, player.current),
            ephemeral=True,
        )

    @app_commands.command(name="pause", description="Hold the melody mid-phrase")
    async def pause(self, interaction):
        player = self.get_guild_player(interaction.guild)
        if not player or not player.current or player.paused:
            return await interaction.response.send_message(
                embed=error_embed(say(NOT_PLAYING_LINES)),
                ephemeral=True,
            )

        await player.pause(True)
        await self.refresh_panel(interaction.guild.id, note=say(PAUSE_LINES))
        await interaction.response.send_message(
            embed=status_embed("Melody Paused", say(PAUSE_LINES)),
            ephemeral=True,
        )

    @app_commands.command(name="resume", description="Continue the paused melody")
    async def resume(self, interaction):
        player = self.get_guild_player(interaction.guild)
        if not player or not player.paused:
            return await interaction.response.send_message(
                embed=error_embed(say(NOT_PLAYING_LINES)),
                ephemeral=True,
            )

        await player.pause(False)
        await self.refresh_panel(interaction.guild.id, note=say(RESUME_LINES))
        await interaction.response.send_message(
            embed=status_embed("Melody Resumed", say(RESUME_LINES)),
            ephemeral=True,
        )

    @app_commands.command(name="volume", description="Adjust Dolia's resonance (0-100)")
    @app_commands.describe(level="Volume level from 0 to 100")
    async def volume(self, interaction, level: app_commands.Range[int, 0, 100]):
        player = self.get_guild_player(interaction.guild)
        if not player:
            return await interaction.response.send_message(
                embed=error_embed(say(NOT_PLAYING_LINES)),
                ephemeral=True,
            )

        await player.set_volume(level)
        await self.refresh_panel(
            interaction.guild.id,
            note=f"{say(VOLUME_LINES)} Now set to **{level}%**.",
        )
        await interaction.response.send_message(
            embed=status_embed("Volume Shifted", f"Dolia now sings at **{level}%** volume."),
            ephemeral=True,
        )

    @app_commands.command(name="loop", description="Loop the song or queue")
    @app_commands.describe(mode="off = no loop, track = loop one, queue = loop all")
    @app_commands.choices(
        mode=[
            app_commands.Choice(name="off", value="off"),
            app_commands.Choice(name="track", value="track"),
            app_commands.Choice(name="queue", value="queue"),
        ]
    )
    async def loop(self, interaction, mode: str):
        player = self.get_guild_player(interaction.guild)
        if not player:
            return await interaction.response.send_message(
                embed=error_embed(say(NOT_PLAYING_LINES)),
                ephemeral=True,
            )

        if mode == "track":
            player.queue.mode = wavelink.QueueMode.loop
            note = say(LOOP_TRACK_LINES)
        elif mode == "queue":
            player.queue.mode = wavelink.QueueMode.loop_all
            note = say(LOOP_QUEUE_LINES)
        else:
            player.queue.mode = wavelink.QueueMode.normal
            note = say(LOOP_OFF_LINES)

        await self.refresh_panel(interaction.guild.id, note=note)
        await interaction.response.send_message(
            embed=status_embed("Loop Changed", f"Loop mode is now **{loop_mode_label(player.queue.mode)}**."),
            ephemeral=True,
        )

    @app_commands.command(name="nowplaying", description="See what flows now")
    async def nowplaying(self, interaction):
        player = self.get_guild_player(interaction.guild)
        if not player or not player.current:
            return await interaction.response.send_message(
                embed=error_embed(say(NOT_PLAYING_LINES)),
                ephemeral=True,
            )

        await interaction.response.send_message(
            embed=control_panel_embed(player, interaction.guild, note=say(PLAY_LINES)),
            ephemeral=True,
        )

    @app_commands.command(name="help", description="Open Dolia's command grimoire")
    async def help(self, interaction):
        await interaction.response.send_message(embed=help_embed(), ephemeral=True)


async def setup(bot):
    cog = Music(bot)
    bot.add_view(ControlPanelView(cog))
    await bot.add_cog(cog)
