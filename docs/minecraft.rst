Minecraft Cog
=============

Commands
--------
.. _mc-whitelist:
\/whitelist <player-name>
~~~~~~~~~~~~
Adds player-name to the server whitelist. Only usable by roles in the role whitelist file.

.. _mc-send:
\/send <command>
~~~~~~~~~~~~
Sends a sanitized command to the server console. Only usable by server administrators.

.. _mc-list:
\/list
~~~~~~~~~~~~
Lists online players in a channel linked to a Minecraft server.

Log Filter
----------
Type Detection
~~~~~~~~~~~~~~
Pinebot uses context to detect the following message types:
    * Connection  (Join or Leave)
    * Achievement
    * Challenge
    * Death
    * Chat Message
Notes for filter improvement:
    * Multi-server type detection (Paper, Spigot, Forge, Vanilla)
    * Death message detection improvement (Currently searches long list)
    * Achievement & Challenge analytics