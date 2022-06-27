# Pinebot

Pinebot is a passion project I started to bring together my many gameservers into one place.
For a long time I wondered about creating an environment in discord that showed when friends were online. Additionally, whitelisting players from my phone was desirable, since I'm not always at home. This small project quickly grew in scope as I slowly realized there was a lot I could do with
an integration of systems like this, and this is the manifestation of that. 


# Features
## Playtime Logging
If you played, Pinebot knows when and for how long. Makes great statistics, and to know when your friend isn't taking a breakup too well.

## Remote Console Access
Securely send commands from the comfort of your own discord server. Using server permissions, assign certain commands to certain roles on the server.

## Account Link
Linked accounts allow for totaling playtime of a user, automating whitelisting across a server network, and more.
Currently not implemented, features that depend on Account Link are to be finalized.

# Commands
- `>playtime` reports playtime for user on server, and the first day online. Requires having linked accounts.
    - With a  `<user>` arg, lists playtime of that discord user, listing their top 3 played on servers and a total playtime. Requires linked accounts.
    - With a `<server>` arg, lists playtime of a username or uuid on that server. Works with unlinked accounts

# Supported Games

## Minecraft
Should support all vanilla minecraft versions (untested), though modded versions may require a custom cog to be made for chat filtering.
This cog is built to use [itzg's docker minecraft server](https://github.com/itzg/docker-minecraft-server). 

### Subcommands
#### User
- `>list` lists online players
#### Admin
- `>sendcmd <>` sends command to corresponding channel
- `>whitelist <playername>` whitelists player on that server

## Factorio
- To be finalized

## Starbound
- To be implemented