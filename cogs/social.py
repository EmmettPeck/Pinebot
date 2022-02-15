import discord
from discord.ext import commands

class SocialCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # Hello!       
    @commands.Cog.listener()
    async def on_message(self, message): 
        '''Responds Hello! To messages that start with Hi, hi, Hello, hello'''
        if message.author == self.bot.user:
            return

        if message.content.startswith('hello') | message.content.startswith('hi') | message.content.startswith('Hello')| message.content.startswith('Hi'):
            await message.channel.send('Hello!')
            
def setup(bot):
    bot.add_cog(SocialCog(bot))        