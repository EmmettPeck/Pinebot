"""
A cog for discord.py that carries an assortment of utility commands for Pineserver

Authors: Emmett Peck (EmmettPeck)
Version: July 19th, 2022
"""
from discord.ext import commands


from database import DB
from embedding import embed_server_list, embed_build

class Utilities(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
    # GetID --------------------------------------------------------------------------------------------------------------------------------------------------
    @commands.command(name='getID',help='Returns current channel ID',brief='Returns channel ID', hidden=True)
    async def getID(self, ctx):
        ''' Command which returns current channel ID'''
        await ctx.send(ctx.channel.id)

    # ServerList --------------------------------------------------------------------------------------------------------------------------------------------------
    @commands.command(name='serverlist', help="Lists all currently registered servers, whitelist may be required to join", brief="Lists all pineserver.net servers")
    async def server_list(self, ctx):
        out_dict = []
        for col in DB.mongo['Servers'].list_collection_names():
            for server in col.find({"hidden":True}):
                out_dict.append({'name':server.get('name'),'desc':server.get('description'),'ip':server.get('ip'),'version':server.get('version')})

        await ctx.send(embed=embed_server_list(reference=ctx.author,input=out_dict))

def setup(bot):
    bot.add_cog(Utilities(bot))