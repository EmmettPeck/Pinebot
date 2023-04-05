.. _accounts:

Accounts
========
Discord cog to manage tying game accounts to Discord user accounts using proof.

This proof is achieved by having the user send a randomized 5-digit code through
the corresponding service's chat to prove the discord user has access to the 
account, or the account is consenting to being linked to the service.

Link Keys
---------
Link keys are dictionaries generated from the database, and stored for 5 minutes. These keys are used when confirming an account code is correct.

Link Command
----
> Usage `\/link`

Attempts to link a discord account to a gameserver account. Must be sent in a bridged discord channel. 

* Sends a private message with a link key. 
* If a valid link key is sent in the game channel, a link account entry is added to the server collection.

Unlink Command
------
> Usage `\/unlink <account-name>`

Unlinks `account-name` from a bridged discord channel.
