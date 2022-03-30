"""I'm not sure how yet, but breakout a listener thread for each server using dockingPort, then act on returns"""
import discord
from discord.ext import tasks, commands

from dockingPort import DChannels, DockingPort
from messages import MessageType

class ChatLink(commands.Cog):

    def __init__(self, bot):
        self.dockingPort=DockingPort()
        self.bot = bot
        self.pass_mc_message.start()

    def cog_unload(self):
        self.pass_mc_message.cancel()

    def get_out_str(self, item):
        """Message Type Sort and Formatting """
        user = item.get("username")
        msg = item.get("message")

        if(item.get("type") == MessageType.MSG):
            out_str = f"```yaml\n💬 <{user}> {msg}\n```"
        elif(item.get("type") == MessageType.JOIN or item.get("type") == MessageType.LEAVE):
            out_str = f"```fix\n🚪 {user} {msg}\n```"
        elif item.get("type") == MessageType.DEATH:
            out_str = f"```💀 {user} {msg}```"
        else:
            out_str = ""
            print("ERROR: out_str fallthrough")
        return out_str

    # Chat-Link
    # ------------------------------------------------------------------
    @tasks.loop(seconds=0.5)
    async def pass_mc_message(self):

        for server in DChannels.get_channels():
            server_index = DChannels.get_channels.index(server)
            queue = DockingPort.get_msg_queue(server_index)
            out_channel = self.bot.get_channel(server["id"])

            while not queue.empty():
                item = queue.get()
                out_str = self.get_out_str(item)
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
        for channel in DChannels.get_channels():
            cid = channel.get("channel_id")
            if message.channel.id == cid:
                
                # Send message to mc server! Use colored messages?
                item = f"<{message.author.name}> {message.content}"
                DockingPort.send(cid, f'tellraw @a {{"text":"{item}","color":"#7289da"}}',False)

def setup(bot):
    bot.add_cog(ChatLink(bot))        