import json
import time

import discord
from discord.ext import commands

from bot.utils.format import send_embed


async def sql_write(ctx, column, string):
    cursor = await db.execute(f"Select {column} from AutoMod where GuildID = ?", (ctx.guild.id,))
    result = await cursor.fetchone()

    if result == ():
        await db.execute("Insert into AutoMod values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                         (ctx.guild.id, False, False, False, False, False, False, False, False))
        await db.commit()
        await db.execute(f"Set {column} = ? where GuildID = ?", (True, ctx.guild.id))
        await db.commit()
        return await send_embed(ctx, f"Turned on detection for {string}.")

    if result[0]:
        await db.execute(f"Update AutoMod set {column} = ? where GuildID = ?", (False, ctx.guild.id))
        await db.commit()
        return await send_embed(ctx, f"Turned off detection for {string}.")

    else:
        await db.execute(f"Update AutoMod set {column} = ? where GuildID = ?", (True, ctx.guild.id))
        await db.commit()
        return await send_embed(ctx, f"Turned on detection for {string}.")


class AutoMod(commands.Cog, name="AutoMod"):
    def __init__(self, bot):
        self.bot = bot
        global db
        db = self.bot.db

    # Banned words command is in guildsetup, because I'm too lazy to move it here along with the rest of the DB
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @commands.group(invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def automod(self, ctx):
        """Get AutoMod settings for this server."""

        try:
            result = self.bot.automod[ctx.guild.id]
        except KeyError:
            self.bot.automod[ctx.guild.id] = [True for i in range(8)]
            result = None

        if not result:
            await db.execute("Insert into AutoMod values (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                             (ctx.guild.id, False, False, False, False, False, False, False, False))
            await db.commit()
            result = [False, False, False, False, False, False, False, False]

        a = result.copy()

        for i, v in enumerate(a):
            if v:
                a[i] = "On"
            else:
                a[i] = "Off"

        description = f"**All Caps Detection:** {a[0]}\n" \
                      f"**Fast Message Spam Detection:** {a[1]}\n" \
                      f"**Discord Invite Detection:** {a[2]}\n" \
                      f"**Link Detection:** {a[3]}\n" \
                      f"**Mass Mention Detection:** {a[4]}\n" \
                      f"**Emoji Spam Detection:** {a[5]}\n" \
                      f"**Spoiler Detection:** {a[6]}\n" \
                      f"**Selfbot Detection:** {a[7]}\n"

        embed = discord.Embed(
            colour=discord.Colour.blue(),
            title="AutoMod Settings",
            description=description
        )
        embed.set_author(name=str(ctx.author), icon_url=str(ctx.author.avatar_url))

        await ctx.send(embed=embed)

    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @automod.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def ignore(self, ctx, channel: discord.TextChannel = None):
        """Ignore a text channel for automod, or unignore it.."""

        if not channel:
            channel = ctx.channel

        cursor = await db.execute("Select count(ChannelID) from AutoModIgnoredChannels where GuildID = ?",
                                  (ctx.guild.id,))
        result = await cursor.fetchone()

        if not result[0]:
            await db.execute("Insert into AutoModIgnoredChannels values (?, ?)", (ctx.guild.id, channel.id,))
            await db.commit()

            self.bot.automodignoredchannels[ctx.guild.id] = [channel.id]

            await send_embed(ctx, "Ignored channel for automod.")

        else:
            await db.execute("Delete from AutoModIgnoredChannels where ChannelID = ? and GuildID = ?",
                             (channel.id, ctx.guild.id))
            await db.commit()

            self.bot.automodignoredchannels[ctx.guild.id].remove(channel.id)

            await send_embed(ctx, "Unignored channel for automod.")

    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @automod.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def allcaps(self, ctx):
        """Toggle all caps detection on or off. Removes message if detected."""

        try:
            self.bot.automod[ctx.guild.id][0] = not self.bot.automod[ctx.guild.id][0]
        except KeyError:
            self.bot.automod[ctx.guild.id] = [False if i != 0 else True for i in range(8)]

        await sql_write(ctx, "AllCaps", "all caps")

    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @automod.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def fastmessagespam(self, ctx):
        """Toggle fast message spam detection on or off. 15 minute mute is the punishment unless the server doesn't have
        a designated mute role or bot doesn't have permission to add roles."""

        try:
            self.bot.automod[ctx.guild.id][1] = not self.bot.automod[ctx.guild.id][1]
        except KeyError:
            self.bot.automod[ctx.guild.id] = [False if i != 1 else True for i in range(8)]

        await sql_write(ctx, "FastMessageSpam", "fast message spam")

    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @automod.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def discordinvites(self, ctx):
        """Toggle discord invite detection on or off. Removes message if detected."""

        try:
            self.bot.automod[ctx.guild.id][2] = not self.bot.automod[ctx.guild.id][2]
        except KeyError:
            self.bot.automod[ctx.guild.id] = [False if i != 2 else True for i in range(8)]

        await sql_write(ctx, "DiscordInvites", "discord invites")

    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @automod.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def links(self, ctx):
        """Toggle link detection on or off. Removes message if detected."""

        try:
            self.bot.automod[ctx.guild.id][3] = not self.bot.automod[ctx.guild.id][3]
        except KeyError:
            self.bot.automod[ctx.guild.id] = [False if i != 3 else True for i in range(8)]

        await sql_write(ctx, "Links", "links")

    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @automod.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def massmention(self, ctx):
        """Toggle mass mention detection on or off. Removes message and mutes member for 15 minutes if detected."""

        try:
            self.bot.automod[ctx.guild.id][4] = not self.bot.automod[ctx.guild.id][4]
        except KeyError:
            self.bot.automod[ctx.guild.id] = [False if i != 4 else True for i in range(8)]

        await sql_write(ctx, "MassMention", "mass mentions")

    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @automod.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def emojispam(self, ctx):
        """Toggle emoji spam detection on or off. Removes message if detected."""

        try:
            self.bot.automod[ctx.guild.id][5] = not self.bot.automod[ctx.guild.id][5]
        except KeyError:
            self.bot.automod[ctx.guild.id] = [False if i != 5 else True for i in range(8)]

        await sql_write(ctx, "EmojiSpam", "emoji spam")

    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @automod.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def spoilers(self, ctx):
        """Toggle spoiler detection on or off. Removes message if detected."""

        try:
            self.bot.automod[ctx.guild.id][6] = not self.bot.automod[ctx.guild.id][6]
        except KeyError:
            self.bot.automod[ctx.guild.id] = [False if i != 6 else True for i in range(8)]

        await sql_write(ctx, "Spoilers", "spoilers")

    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    @automod.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def selfbot(self, ctx):
        """Toggle selfbot detection on or off. Bans member if detected."""

        try:
            self.bot.automod[ctx.guild.id][7] = not self.bot.automod[ctx.guild.id][7]
        except KeyError:
            self.bot.automod[ctx.guild.id] = [False if i != 7 else True for i in range(8)]

        await sql_write(ctx, "Selfbot", "selfbots")
