"""
minecraft.py
By: Emmett Peck
A cog for discord.py that incorporates docker chatlink, header updating, and playtime logging.
"""
import logging
import discord
from discord.ext import commands
from discord.ext.commands import has_permissions, CheckFailure
from database import DB
from messages import MessageType, get_between, get_msg_dict, split_first
from username_to_uuid import UsernameToUUID
from server import Server
from embedding import embed_build
import analytics_lib 


from cogs.gamecog import GameCog


class Minecraft(GameCog):

# COMMANDS ---------------------------------------------------------------------
    # Whitelist ----------------------------------------------------------------
    @commands.command(name='whitelist', help=f"Usage: >whitelist <arg>. Requires a {DB.get_role_whitelist()} role.", brief="Whitelist a player.")
    @commands.has_any_role(*DB.get_role_whitelist())
    async def whitelist(self, ctx, *, mess):
        ''' Whitelists <args> to corresponding server as is defined in DChannels if user has applicable role'''
        # TODO server ARG
        response = self.send(server=self.servers[self.find_server(ctx.channel.id)], command=f"whitelist add {mess}",logging=True)
        if response:
            await ctx.send(response)
        else:
            await ctx.send("Server not found. Use command only in 'Minecraft' text channels.")
    @whitelist.error
    async def whitelist_error(self, error, ctx):
        if isinstance(error, CheckFailure):
            await self.bot.send_message(ctx.message.channel, "You do not have the necessary roles.")

    # Send ---------------------------------------------------------------------
    @commands.command(name='sendcmd', help="Usage: >sendcmd <arg>. Requires administrator permissions.", brief="Sends command to server.")
    @has_permissions(administrator=True)
    async def sendcmd(self, ctx, *, mess):
        ''' Sends <args> as /<args> to corresponding server as is defined in DChannels if user has applicable role'''
        server = self.servers[self.find_server(ctx.channel.id)]
        logging.info(f"{ctx.author} sendcmd {mess} to {server.server_name}")
        response = self.send(server=server, command=mess, log=True)
        logging.info(response)
        if response:
            await ctx.send(response)
            return
        else:
            await ctx.send("Server not found. Use command only in 'Minecraft' text channels.")
            return

    @sendcmd.error
    async def send_error(self, error, ctx):
        if isinstance(error, CheckFailure):
            await self.bot.send_message(ctx.message.channel, "You do not have the necessary permissions.")

    # List ---------------------------------------------------------------------
    @commands.command(name='list', help="Usage `>list` in desired corresponding channel.", brief="Lists online players.")
    async def list(self, ctx):
        response = self.send(server=self.servers[self.find_server(ctx.channel.id)], command="list")
        
        await ctx.message.delete()
        if response:
            await ctx.send(embed=embed_build(message=response, reference=ctx.author))
        else:
            await ctx.send(embed=embed_build("Server not found. Use command only in 'Minecraft' text channels."))

# OVERLOADS ----------------------------------------------------------------------------------

    def get_version(self) -> str:
        return "Minecraft"

    def get_uuid(self, username:str):
        """Get player UUID from username"""
        if username == None:
            return None

        converter = UsernameToUUID(username)
        uuid = converter.get_uuid()
        return uuid

    def get_username_fixes(self) -> tuple:
        return ("<",">")

    def send(self, server:Server, command:str, log=False) -> list: 
        """
        OVERLOAD: 
        Sends command to corresponding ITZD Minecraft docker server. Returns a str output of response.
        """
        filtered = command.replace("'", "'\\''") 
        temp = super().send(server=server,command=f"rcon-cli '/{filtered}'", log=log, filter=False)
        logging.info(f"Minecraft send return: {temp}")
        return temp

    def send_message(self, server:Server, message:str):
        '''
        OVERLOAD: MC
        Sends discord blue message to MC chat
        '''
        self.send(server=server,command=f'tellraw @a {{"text":"{message}","color":"#7289da"}}')

    def get_player_list(self, server:Server) -> list:
        """ OVERLOAD: MC
        get_player_list(self) -> ["Playername", "Playername"...]
        For versions without a getlist function, returns None

        """
        player_list = []
        response = self.send(server=server,command="list")

        # Response Catch
        if not response:
            logging.error(f'get_player_list got False evaluating response {response}')
            return None

        # Unsafe Player_Max Split
        player_max = int(response.split("max of")[1].split()[0])
        logging.debug(f"{server.server_name} player_max={player_max}")
        server.player_max = player_max

        # Break Apart Onlineplayer name strings
        stripped = response.split("online:")[1].strip()
        try:
            for player in stripped.split(','):
                player_list.append(player.strip())
        except IndexError:
            logging.warning(f'IndexError in get_player_list for {server.server_name} while splitting response:{response}, playerlist:{player_list}')
            return None
        else:
            if player_list == ['']: 
                logging.debug(f'get_player_list: No players online {server.server_name}')
                return None
            return player_list

    def is_player_online(self, server:Server,  playername:str) -> bool:
        """
        OVERLOAD: Minecraft
        If uuid_index or playername in online_players: Returns True, else False
        """
        for player in server.online_players:
            if playername == player: 
                logging.debug(f"is_player_online {playername} is online {server.server_name}")
                return True
        return False

    # Filter--------------------------------------------------------------------------------------------------------------------------------------------
    def filter(self, server:Server, message:str, ignore=False):
        """ 
        OVERLOAD: Minecraft 1.18.2 Filter
        Filters logs by to gameversion, adding leaves/joins to connectqueue and messages to message queue
        """
        # Fingerprint Filtering
        if server.fingerprint.is_unique_fingerprint(message):
            post = None

            # Ensure '[Server thread/INFO]:' ----------------------------------------------------------------------
            info_split = message.split('] [Server thread/INFO]',1)
            if len(info_split) != 2:
                return

            # Separate time; break apart entry from info ----------------------------------------------------------
            entry = split_first(info_split[1],':')[1].strip()
            time = split_first(info_split[0], '[')[1]

            # Message Detection using <{user}> {msg} --------------------------------------------------------------
            if (entry[0] == '<') and ('<' and '>' in entry):
                msg  = split_first(entry,'> ')[1]
                user = get_between(entry, '<','>')
                post = get_msg_dict(user, msg, MessageType.MSG, discord.Color.green())

            # Join/Leave Detection by searching for "joined the game." and "left the game."------------------------
            elif entry.find(" joined the game") >= 0: 
                msg = "joined the game"
                user = entry.split(' ',1)[0]
                post = get_msg_dict(user, msg, MessageType.JOIN, discord.Color.dark_teal())
            elif entry.find(" left the game") >= 0:
                msg = "left the game"
                user = entry.split(' ',1)[0]
                post = get_msg_dict(user, msg, MessageType.LEAVE, discord.Color.dark_teal())

            # Achievement Detection ------------------------------------------------------------------------------
            elif entry.find("has made the advancement") >= 0:
                user = entry.split(' ',1)[0]
                msg = f"has made the advancement [{split_first(entry,'[')[1]}"
                post = get_msg_dict(user, msg, MessageType.ACHIEVEMENT, discord.Color.gold())

            # Challenge Detection --------------------------------------------------------------------------------
            elif entry.find("has completed the challenge") >= 0:
                user = entry.split(' ',1)[0]
                msg = f"has completed the challenge [{split_first(entry,'[')[1]}"
                post = get_msg_dict(user, msg, MessageType.ACHIEVEMENT, discord.Color.dark_purple())

            # Death Message Detection ----------------------------------------------------------------------------
            else:
                dm = Death(entry)
                if dm.is_death():
                    post = get_msg_dict(dm.player, dm.stripped_msg, MessageType.DEATH, discord.Color.red())

            # If Not Ignore, Messages are sent and accounted for playtime
            if post and (not ignore):
                if post.get('type') == MessageType.JOIN or post.get('type') == MessageType.LEAVE:
                    post["server"] = server.server_name
                    server.connect_queue.put(post)
                server.message_queue.put(post)

# Deaths--------------------------------------------------------------------------------------------------------------------------------------------
class Death:
    """Filters death messages using startswith and possible MC death messages"""

    def __init__(self, msg):
        self.msg = msg.strip()
        self.player = self.msg.split()[0]
        self.stripped_msg = self.msg.split(self.player)[1].strip()
        self.death_msg_startw = ["was shot by","was pummeled by","was pricked to death","walked into a cactus whilst trying to escape","drowned","drowned whilst trying to escape","experienced kinetic energy","experienced kinetic energy whilst trying to escape","blew up","was blown up by","was killed by","hit the ground too hard","fell from a high place","fell off a ladder","fell off some vines","fell off some weeping vines","fell off some twisting vines","fell off scaffolding","fell while climbing","was impaled on a stalagmite","was squashed by a falling anvil","was squashed by a falling block","was skewered by a falling stalactite","went up in flames","burned to death","was burnt to a crisp whilst fighting","went off with a bang","tried to swim in lava","was struck by lightning","discovered the floor was lava","walked into danger zone due to","was killed by magic","was killed by","froze to death","was frozen to death by","was slain by","was fireballed by","was stung to death","was shot by a skull from","starved to death","suffocated in a wall","was squished too much","was squashed by","was poked to death by a sweet berry bush","was killed trying to hurt","was impaled by","fell out of the world","didn't want to live in the same world as","withered away","died from dehydration","died","was roasted in dragon breath","was doomed to fall","fell too far and was finished by","was stung to death by","went off with a bang","was killed by even more magic","was too soft for this world","was obliterated by a sonically-charged shriek"]

    def is_death(self):
        """Checks if playerless string matches death message"""
        for item in self.death_msg_startw:
            if self.stripped_msg.startswith(item):
                return True
        return False

# ------------------------------------------------------------------------------------------------------------------------------------------------

def setup(bot):
    bot.add_cog(Minecraft(bot))