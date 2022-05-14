"""
chatLink.py
By: Emmett Peck
A cog for discord.py that incorporates 
"""
from discord.ext import tasks, commands

from messages import MessageFilter
from database import DB
from dockingPort import DockingPort
from embedding import embed_message

class ChatLink(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        # Fingerprint All Old Messages
        for server in DB.get_containers():
            DockingPort().read(server.get("channel_id"), True)
        # TODO Check if players are online that there isn't a join for, if so, add a join at time of discovery

        self.pass_message.start()

    def cog_unload(self):
        self.pass_message.cancel()

    # Chat-Link
    # ------------------------------------------------------------------
    # Header Updating ------------------------------------------------------------------
        # Docker Status
        # Playercount
            # Version Based (MC List vs Factorio[Generic] version types)
        # MOTD?
        # Update w/ Taskloop

    # Server -> Discord  -----------------------------------------------------------------------
    @tasks.loop(seconds=1)
    async def pass_message(self):
        # For each server, set outchannel, get items from queue
        i = 0 #Server Number
        for server in DB.get_containers():
            id = server.get("channel_id")
            ctx = self.bot.get_channel(id)
            q = DB.get_msg_queue(i)
            DockingPort().read(id)

            # Loop through Queue until empty for each server, printing
            while not q.qsize() == 0: 
                item = q.get()
                await ctx.send(embed=embed_message(item))
            i+=1

    @pass_message.before_loop
    async def before_pass_mc_message(self):
        await self.bot.wait_until_ready() 

    # Discord -> Server -----------------------------------------------------------------------
    @commands.Cog.listener("on_message")
    async def on_disc_message(self, message):
        # Check to make sure it isn't a bot message or command
        if message.author.bot or message.content.startswith('>'):
            return

        # Check against channel ids
        for channel in DB.get_containers():
            cid = channel.get("channel_id")
            if message.channel.id == cid:
                # Catch non-mc messages
                if channel.get("version") != "mc": return
                # Send message to mc server! Use colored messages?
                item = f"<{message.author.name}> {message.content}"
                print(f" -Discord-: {item}")
                DockingPort().send(cid, f'tellraw @a {{"text":"{item}","color":"#7289da"}}',False)

def setup(bot):
    bot.add_cog(ChatLink(bot))        