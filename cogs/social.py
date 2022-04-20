"""Social Cog --- Hello!"""

from discord.ext import commands

class Social(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # Hello!       
    @commands.Cog.listener("on_message")
    async def on_hello(self, message): 
        '''Responds Hello! To messages that start with Hi, hi, Hello, hello'''
        if message.author == self.bot.user:
            return

        # Prevent hellos in mc channels because it's annoying
        for channel in DChannels.get_channels():
            if message.channel.id == channel.get("channel_id"):
                return

        if message.content.startswith('hello') | message.content.startswith('hi') | message.content.startswith('Hello')| message.content.startswith('Hi'):
            await message.channel.send('Hello!')

def setup(bot):
    bot.add_cog(Social(bot))        