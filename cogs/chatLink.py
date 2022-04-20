"""
chatLink.py
By: Emmett Peck
A cog for discord.py that incorporates 
"""
from discord.ext import tasks, commands

from messages import MessageType

import queue # imported for using queue.Empty exception

class ChatLink(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.pass_message.start()

    def cog_unload(self):
        self.pass_message.cancel()

    def format_message(self, item):
        """Message Type Sort and Formatting """
        try:
            user = item.get("username")
            msg = item.get("message")
        except AttributeError:
            return None
        else:
            if   item.get("type") == MessageType.MSG:
                out_str = f"```yaml\n💬 <{user}> {msg}\n```"
            elif item.get("type") == MessageType.JOIN or item.get("type") == MessageType.LEAVE:
                out_str = f"```fix\n🚪 {user} {msg}\n```"
            elif item.get("type") == MessageType.DEATH:
                out_str = f"```💀 {user} {msg}```"
            else:
                out_str = ""
                print("ERROR: out_str fallthrough")
            return out_str

    # Chat-Link
    # ------------------------------------------------------------------
    @tasks.loop(seconds=5)
    async def pass_message(self):
        # For each server, set outchannel, get items from queue
        i = 0 #Server Number
        channels = DChannels.get_channels()
        for server in channels:
            q = DockingPort.get_msg_queue(i) 
            out_channel = self.bot.get_channel(server.get("id"))

            # Try to get from queue, if empty moves to next server, otherwise formats and sends str
            try:
                item = q.get()
            except queue.Empty:
                i+1
                continue
            else:  
                out_str = self.format_message(item)
                if out_str: await out_channel.send(out_str)
            i+=1
    @pass_message.before_loop
    async def before_pass_mc_message(self):
        await self.bot.wait_until_ready() 

    @commands.Cog.listener("on_message")
    async def on_disc_message(self, message):
        # Check to make sure it isn't a bot message or command
        if message.author == self.bot.user or message.content.startswith('>'):
            return

        # Check against channel ids
        for channel in DChannels.get_channels():
            cid = channel.get("channel_id")
            if message.channel.id == cid:
                
                # Send message to mc server! Use colored messages?
                item = f"<{message.author.name}> {message.content}"
                DockingPort.send(cid, f'tellraw @a {{"text":"{item}","color":"#7289da"}}',False)

def setup(bot):
    bot.add_cog(ChatLink(bot))        