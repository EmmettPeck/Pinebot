

# Pinebot
<p align="left">
    <a href="https://www.python.org/">
    <img src="https://img.shields.io/static/v1?label=Python&message=3.8 | 3.9 | 3.10&color=?style=flat&logo=python"
         alt="dependencies">
  </a>
  <a href="https://github.com/docker/docker-py">
    <img src="https://img.shields.io/static/v1?label=Docker Python SDK&message=6.0.0&color=?style=flat&logo=docker"
         alt="dependencies">
  </a>
  <a href="https://github.com/Rapptz/discord.py">
    <img src="https://img.shields.io/static/v1?label=discord.py&message=deprecated&color=red&?style=flat&logo=python"
         alt="dependencies">
  </a>
</p>

<p align="left">
  <a href="#key-features">Key Features</a> •
  <a href="#set-up">Set Up</a> •
  <a href="#how-it-works">How It Works</a> •
  <a href="#commands">Commands</a> •
  <a href="#development">Development</a> •
  <a href="#credits">Credits</a> •
  <a href="#license">License</a>
</p>

> This project is being rewritten with [pycord](https://github.com/Pycord-Development/pycord) after [discord.py](https://github.com/Rapptz/discord.py) was deprecated; Some features may be outdated or not work as intended.

Pinebot is a Discord bot which reads and reacts to events on connected Docker game servers. From linking channels by passing new messages to other mediums, keeping track of when players leave and join, to providing a secure way of passing commands and messages to a gameserver console through use of role restricted Discord commands.

## Key Features
* Combines chatrooms across platforms
* Playtime logging 
* Remote console access
* Conditional Rolebased Console access
* Configurable Docker log filtering

## Set Up
Currently this application only works with [itzg's dockerized minecraft server](https://github.com/itzg/docker-minecraft-server) running vanilla Minecraft servers. An example docker-compose file can he found [here](https://github.com/EmmettPeck/Pinebot/blob/main/compose.yml).

To clone, build, and run this application, you'll need [Git](https://git-scm.com) and [Docker](https://docs.docker.com/engine/install/) installed on your computer. From your command line: 

```bash
# Clone this repository
$ git clone https://github.com/EmmettPeck/Pinebot

# Go into the repository
$ cd Pinebot

# Place Discord Bot Key into ".env" file
$ echo "TOKEN=REPLACE-WITH-TOKEN" >> .env

# Build Docker Image
$ docker build pinebot .

# Start Docker Compose Services
$ docker compose compose.yml up -d
```
> **Note**
> This guide is only tailored for linux systems running a bash kernel.

### Linking A Channel
In a server with a bot connected to your bot token, link the running gameserver container to a Discord channel. 
`>addserver <name> <Minecraft:version> <container_name> <ip> <description>`

>**Example:** `>addserver example Minecraft:1.19 examples_mc localhost:25565 this is an example!`

## How It Works
- By connecting in a Docker network, the Pinebot container is able to read the log files of connected gameserver containers.

- By linking a Discord channel using the `>addserver` command and providing the name of a running container, Pinebot will begin to read the logs.

- Using the version supplied in the `>addserver` command, Pinebot filters the logs using version specific criteria, and enables game specific commands in that channel.

## Commands
> Most commands can only be used in discord channels [linked](#linking-a-channel) to game servers.
- `>playtime <server> <user>` reports a player's total time playing on a server.
- `>list` lists a linked server's online players
- `>sendcmd <command>` sends command to server console. Only usable by server administrators.
- `>whitelist <playername>` whitelists playername on linked server

## Development
Development priority is going to rewriting the project to use MongoDB for more efficient data storage and Pycord for additional discord features.

### Account Link
Allows Discord users to link multiple game server accounts.

Linked accounts allow for totaling playtime of a user, automating whitelisting across a server network, and more.

### Other Games
Support for the following game servers are planned:
- [Starbound](https://github.com/Didstopia/starbound-server)
- [Factorio](https://github.com/factoriotools/factorio-docker)
- Insurgency\: Sandstorm
- [Additional Minecraft Server Types & Versions](https://hub.docker.com/r/itzg/minecraft-server/tags)

## Credits

This software uses the following open source packages:

- [Docker Python SDK](https://github.com/docker/docker-py)
- [discord.py](https://github.com/Rapptz/discord.py)
- [python-dotenv](https://github.com/theskumar/python-dotenv)

This software is built to run alongsize the following open source applications:
- [itzg's docker-minecraft-server](https://github.com/itzg/docker-minecraft-server)

## License
This repository currently has no license.

---

