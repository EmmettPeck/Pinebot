# Pinebot

A simple discord bot to whitelist players via discord.

Apart of a movement to transfer mc.nikesexparty.net to mc.pineserver.net, and provide a fully accesible archive of major servers hosted.

> Vanilla 2021+,
> Vanilla 2019,
> Vanilla 2018,
> Others

This is to be achieved using [itzg's docker minecraft server](https://github.com/itzg/docker-minecraft-server) and the autopause option whenever possible, as versions 1.18+ dislike the option in my experimenting.

---

## Launch Event

- A small gameplay event on Vanilla 2021+ which begins with PineBot "assimilating" the server away from 1917 roleplay. Players fight a more difficult ender dragon with additional phases/dangers, including a phase which spawns agroed enderman with special drops.
- Server Icon is changed to a purplish corrupted version of the future Pineserver Icon
- After an amount of time, PineBot drops an invite link in the discord channel, ending the event.
  
### Datapack

Will need to write a small datapack or interface with PineBot through rcon commands, somehow.

---

## TO/DO

- Move TO/DO to issue tracker
- Chat-Link
- Player activity presence/tracking [Logging on/off, who, when] chat channel presence
- List command analytics function & info handling

### Discord Channel

- Update code comments to be more concise and legible/organized
- "Start Here" Channel Minecraft
- Permission testing
- Moderator Role
- Moderator only chat which outlines perfered actions of moderators around innapropriate images/conversations
- Rules page & Chat filtering (Via discord if possible)
- Icons

### Pinecone

- Implement autobackups
- Manage diskspace issues
- Auto sync backups to archive drives on main PC?
  - Sync Onedrive backups to archive drives?

### Social Cog

- Coinflip command

### Music Cog

- Music bot

### Utils Cog

- Purge x chats admin command
- AddMCServerDict
  - > Append dictionary -> Save -> Run load_mc_Channels

- AddWhitelistRole command
  - > Append to json -> Reload cog? Unsure of how its dealt with with global vars
  
### DockingPort

- Explore await command with subprocess.Popen
