Gamecog
=======
This Baseclass is used for specific game cog implementations.

A cog is a module that integrates with discord-py's event scheduler, allowing multiple modules to function independently.

Bridges a game channel and a discord channel.

.. toctree::
   :maxdepth: 2
   :caption: Child classes

   minecraft
   factorio

.. toctree::
   :maxdepth: 2
   :caption: Internal

   identifiers

Currently Handles
* Channel header updates with playercount and status
   (`header_update()`, `update_channel_header()`)
* Online player list (length is count) 
   (`get_player_list()` & `is_player_online()`)
* Reading container logs on a set interval
   (`read_messages()`, `read()`)
* Filtering container logs
   (`filter`())
   * Operating filter output queue
      (`handle_message()`)                          
   * Adding new players to database
      (`handleconnection()`)
* Changing existing playernames to match accountID
   (`get_uuid()`)
* Sending messages to container stdin
   (`send()`)
* Event on discord messages to send to contianer stdin
   (`on_disc_message()`)

**ACTION: Needs refactoring into subclasses**