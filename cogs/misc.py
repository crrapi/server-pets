import traceback

import os
import codecs
import pathlib
import json


import discord
from discord.ext import commands

from utils.converters import CommandOrCog
from utils.paginator import EmbedPaginator

class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.dblpy = bot.dbl

        self.ignored_cogs = ["jishaku", "handlers", "accountearnmanager", "petmanager", "usagemanager", "shopmanager", "kennelmanager"]
    
    async def fetch_lines(self):
        """Returns a tuple for lines and comments"""
        total = 0
        file_amount = 0
        comments = 0
        functions = 0

        for path, _, files in os.walk("."):
            if "env" in os.environ.keys():
                if path.startswith(os.environ.get("env")):
                    continue
            
            for name in files:
                if name.endswith(".py"):
                    file_amount += 1
                    with codecs.open("./"+ str(pathlib.PurePath(path, name)), "r", "utf-8") as f:
                        for i, l in enumerate(f):
                            if l.strip().startswith("#"):
                                comments += 1
                            if l.strip().startswith("def") or l.strip().startswith("async def"):
                                functions += 1
                            else:
                                total += 1
        
        return (total, comments, functions, file_amount)

    async def fetch_pets(self):
        """Gets the total number of pets"""
        pets = await self.bot.db.fetch("SELECT * FROM pets")

        return len(pets)
    
    async def fetch_commands_used(self):
        """Get the total number of successful commands run"""
        return sum(value for _, value in self.bot.usage.items())

    async def get_paramaters(self, paramaters):
        """Returns a commands peramaters in the format of <> or []"""
        final_string = []

        for paramater in paramaters:
            if "=" in str(paramaters[paramater]):
                final_string.append(f"[{paramater}]")
            else:
                final_string.append(f"<{paramater}>")
        
        return " ".join(final_string)

    @commands.command(name="ping")
    async def ping_(self, ctx):
        """Get the bot's latency"""
        return await ctx.send(f"{round((self.bot.latency*1000))}ms")

    @commands.command(name="about", aliases=["info"])
    async def about(self, ctx):
        """Some info about the bot"""
        try:
            lines = await self.fetch_lines()
            accounts = await self.bot.db.fetch("SELECT * FROM accounts")
            total_pets = await self.fetch_pets()
            
            embed = discord.Embed(title="About Server Pets", colour=discord.Colour.blue(), timestamp=ctx.message.created_at)

            embed.set_footer(text="Hosted by MrRandom#4847")
            embed.set_thumbnail(url=ctx.guild.me.avatar_url)

            embed.add_field(name="Bot Users", value=len(self.bot.users))

            embed.add_field(name="Guilds", value=len(self.bot.guilds))

            embed.add_field(name="Total Line Count", value=lines[0])
            embed.add_field(name="Total Comment Count", value=lines[1])
            embed.add_field(name="Total Function Count", value=lines[2])
            embed.add_field(name="Total File Count", value=lines[3], inline=False)

            embed.add_field(name="Total Registered Users", value=len(accounts) if len(accounts) > 0 and accounts else "None")
            embed.add_field(name="Total Adopted Pets", value=total_pets if total_pets > 0 else "None")
            embed.add_field(name="Total successful commands run", value=await self.fetch_commands_used())

            embed.add_field(name="Quick Links", value="[Support Server](https://discord.gg/kayUTZm) | [Bot Invite](https://discordapp.com/api/oauth2/authorize?client_id=502205162694246412&permissions=262176&scope=bot) | [Source Code](https://github.com/lganwebb/server-pets) | [Discord Bot List](https://discordbots.org/bot/502205162694246412) | [Vote](https://discordbots.org/bot/502205162694246412/vote)")
            return await ctx.send(embed=embed)
        except Exception:
            traceback.print_exc()

    @commands.command(name="help")
    async def help_(self, ctx, command_or_cog:CommandOrCog=None):
        """Get help on a command or cog, or everything"""
        fetched_command_or_cog = "None" if command_or_cog is None else command_or_cog
        
        if command_or_cog != None and fetched_command_or_cog is None:
            return await ctx.send("That command or cog is not found.")

        if command_or_cog is None:
            embeds = []

            for cog in self.bot.cogs:
                if cog.lower() in self.ignored_cogs:
                    continue

                embed = discord.Embed(title=f"Server Pets Help | {cog}", colour=discord.Colour.blue(), timestamp=ctx.message.created_at)
                embed.set_thumbnail(url=ctx.guild.me.avatar_url)

                cog = self.bot.get_cog(cog)

                for command in cog.walk_commands():
                    params = await self.get_paramaters(command.clean_params)
                    if len(command.aliases) > 0:
                        to_add = [command.name]
                        for alias in command.aliases: to_add.append(alias)
                        embed.add_field(name=f"{command.parent if command.parent else ''} [{', '.join(to_add)}] {params}", value=command.help)
                    else:
                        embed.add_field(name=f"{command.parent if command.parent else ''} {command.name} {params}", value=command.help)
                
                embed.set_footer(text="To zoom in on a command or cog, use `p-help {command/cog}`")
                
                embeds.append(embed)
            
            return await ctx.paginate(message=None, entries=embeds)

        if isinstance(fetched_command_or_cog, commands.Command):
            command = fetched_command_or_cog
            params = await self.get_paramaters(command.clean_params)

            embed_basic = discord.Embed(title=f"Server Pets Help | {command.name}", colour=discord.Colour.blue(), timestamp=ctx.message.created_at)
            embed_basic.set_thumbnail(url=ctx.guild.me.avatar_url)

            if len(command.aliases) > 0:
                to_add = [command.name]
                for alias in command.aliases: to_add.append(alias)
                embed_basic.add_field(name=f"{command.parent if command.parent else ''} [{', '.join(to_add)}] {params}", value=command.help)
            else:
                embed_basic.add_field(name=f"{command.parent if command.parent else ''} {command.name} {params}", value=command.help)

            embed_other = discord.Embed(title=f"Server Pets Help | {command.name}", colour=discord.Colour.blue(), timestamp=ctx.message.created_at)
            embed_other.set_thumbnail(url=ctx.guild.me.avatar_url)

            if len(command.aliases) == 0:
                embed_other.add_field(name="Aliases", value="None")
            else:
                embed_other.add_field(name="Aliases", value=", ".join(command.aliases))
            embed_other.add_field(name="Parent Command", value=command.parent)

            clean_checks = []
            for check in command.checks:
                clean_checks.append(str(check).split("<function ")[1].split(".")[0].replace("_", " "))

            if len(clean_checks) == 0:
                embed_other.add_field(name="Checks", value="None")
            else:
                embed_other.add_field(name="Checks", value=", ".join(clean_checks))

            embed_basic.set_footer(text="To zoom in on a command or cog, use `p-help {command/cog}`")
            embed_other.set_footer(text="To zoom in on a command or cog, use `p-help {command/cog}`")

            return await ctx.paginate(message=None, entries=[embed_basic, embed_other])
        
        elif isinstance(fetched_command_or_cog, commands.Cog):
            cog = fetched_command_or_cog

            if cog.__class__.__name__.lower() in self.ignored_cogs:
                return await ctx.send("That command or cog is not found.")

            embed = discord.Embed(title=f"Server Pets Help | {cog.__class__.__name__}", colour=discord.Colour.blue(), timestamp=ctx.message.created_at)
            embed.set_thumbnail(url=ctx.guild.me.avatar_url)

            for command in cog.walk_commands():
                params = await self.get_paramaters(command.clean_params)
                if len(command.aliases) > 0:
                    to_add = [command.name]
                    for alias in command.aliases: to_add.append(alias)
                    embed.add_field(name=f"{command.parent if command.parent else ''} [{', '.join(to_add)}] {params}", value=command.help)
                else:
                    embed.add_field(name=f"{command.parent if command.parent else ''} {command.name} {params}", value=command.help)
            
            embed.set_footer(text="To zoom in on a command or cog, use `p-help {command/cog}`")
            return await ctx.send(embed=embed)
    
    @commands.command(name="invites", aliases=["invite"])
    async def invites_(self, ctx):
        """Gives the support server and the bot's invite"""
        try:                       
            embed = discord.Embed(title="Invite Links", description="[Support Server](https://discord.gg/kayUTZm) | [Bot Invite](https://discordapp.com/api/oauth2/authorize?client_id=502205162694246412&permissions=262176&scope=bot)", colour=discord.Colour.blue(), timestamp=ctx.message.created_at)
            embed.set_footer(icon_url=ctx.guild.me.avatar_url)

            return await ctx.send(embed=embed)
        except Exception:
            traceback.print_exc()

def setup(bot):
    bot.add_cog(Misc(bot))
