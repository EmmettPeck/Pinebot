import discord
from discord.ext import tasks, commands
from dockingPort import DockingPort

class SocialCog(commands.Cog):

    def __init__(self, bot):
        self.dockingPort=DockingPort()
        self.bot = bot

    # Hello!       
    @commands.Cog.listener("on_message")
    async def on_hello(self, message): 
        '''Responds Hello! To messages that start with Hi, hi, Hello, hello'''
        if message.author == self.bot.user:
            return

        if message.content.startswith('hello') | message.content.startswith('hi') | message.content.startswith('Hello')| message.content.startswith('Hi'):
            await message.channel.send('Hello!')

    # Chat-Link
    # ------------------------------------------------------------------
    @tasks.loop(seconds = 1) # Accepts floats
    async def pass_mc_message(self):
        # For each channel in channel list look for new msgs, then post
        for channel in self.dockingPort.mc_Channels:
            cid = channnel.get("channel_id")
            info = self.dockingPort.portRead(cid)

            # Print needed messages w/ portsend

    @commands.Cog.listener("on_message")
    async def on_disc_message(self, message):
        # Check to make sure it isn't a bot message or command
        if message.author == self.bot.user or message.content.startswith('>'):
            return
        
        # Check against channel ids
        for channel in self.dockingPort.mc_Channels:
            cid = channel.get("channel_id")
            if message.channel.id == cid:
                
                # Send message to mc server! Use colored messages?
                msg = f"<{message.author.name}> {message.content}"
                self.dockingPort.portSend(cid, f'tellraw @a {{"text":"{msg}","color":"green"}}')

def setup(bot):
    bot.add_cog(SocialCog(bot))        