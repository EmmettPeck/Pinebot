"""I'm not sure how yet, but breakout a listener thread for each server using dockingPort, then act on returns"""
import discord
from discord.ext import tasks, commands

from dockingPort import DockingPort
from messages import MessageType

class ChatLink(commands.Cog):

    def __init__(self, bot):
        self.dockingPort=DockingPort()
        self.bot = bot
        self.pass_mc_message.start()

    def cog_unload(self):
        self.pass_mc_message.cancel()

    # Chat-Link
    # ------------------------------------------------------------------
    @tasks.loop(seconds=0.5)
    async def pass_mc_message(self):
        # For each channel in channel list look for new items, then post
        for mc_channel in self.dockingPort.mc_Channels:
            cid = mc_channel.get("channel_id")
            message_list = self.dockingPort.portRead(cid)

            # Print each message in msglist
            for item in message_list:
                out_channel = self.bot.get_channel(cid)
                user = item.get("username")
                msg = item.get("message")

                # Message Type Sort
                if(item.get("type") == MessageType.MSG):
                    out_str = f"```yaml\n<{user}> {msg}\n```"
                elif(item.get("type") == MessageType.JOIN or item.get("type") == MessageType.LEAVE):
                    out_str = f"```fix\n{user} {msg}\n```"
                elif item.get("type") == MessageType.DEATH:
                    out_str = f"```\n{user} {msg}\n```"
                await out_channel.send(out_str)

    @pass_mc_message.before_loop
    async def before_pass_mc_message(self):
        await self.bot.wait_until_ready() 


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
                item = f"<{message.author.name}> {message.content}"
                self.dockingPort.portSend(cid, f'tellraw @a {{"text":"{item}","color":"#7289da"}}',False)

def setup(bot):
    bot.add_cog(ChatLink(bot))        