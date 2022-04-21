"""
chatLink.py
By: Emmett Peck
A cog for discord.py that incorporates 
"""
from discord.ext import tasks, commands

from messages import MessageFilter

import queue # imported for using queue.Empty exception

from database import DB
from dockingPort import DockingPort

class ChatLink(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.pass_message.start()

    def cog_unload(self):
        self.pass_message.cancel()

    # Chat-Link
    # ------------------------------------------------------------------
    @tasks.loop(seconds=1)
    async def pass_message(self):
        # For each server, set outchannel, get items from queue
        i = 0 #Server Number
        channels = DB.get_containers()
        for server in channels:
            id = server.get("channel_id")
            out_channel = self.bot.get_channel(id)
            q = DB.get_msg_queue(i)
            DockingPort().read(id)

            # Loop through Queue until empty for each server, printing
            while not q.qsize() == 0: 
                item = q.get()
                out_str = MessageFilter().format_message(item)
                if out_str: 
                    await out_channel.send(out_str)
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
        for channel in DB.get_containers():
            cid = channel.get("channel_id")
            if message.channel.id == cid:
                
                # Send message to mc server! Use colored messages?
                item = f"<{message.author.name}> {message.content}"
                DockingPort().send(cid, f'tellraw @a {{"text":"{item}","color":"#7289da"}}',False)

def setup(bot):
    bot.add_cog(ChatLink(bot))        