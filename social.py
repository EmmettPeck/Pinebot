import discord
from discord.ext import commands

class SocialCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # Hello!
    @bot.event 
    async def on_message(message): 
        if message.author == bot.user:
            return

        if message.content.startswith('hello') | message.content.startswith('hi') | message.content.startswith('Hello')| message.content.startswith('Hi'):
            await message.channel.send('Hello!')

        await bot.process_commands(message)

def setup(bot):
    bot.add_cog(SocialCog(bot))        