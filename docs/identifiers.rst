.. _identifiers:

Identifiers
-----------
Identifiers change handling conditions based on confidence in a username or account ID.

Follows three situations:
~~~~~~~~~~~~~~~~~~~~~~~~~
* Centralized means the Username can be matched to an account ID using the web.
* Noncentralized means an account ID exists, but is not always accessable.
* No UUID means an account ID does not exist.

Protocols:
~~~~~~~~~~
1. Centralized
   On command/join get UUID, if UUID matches old UUID with different name change that name to the new name.
2. Noncentralized UUID Unchangable Name 
   Search by name, save UUID when available.
3. Noncentralized UUID Changable Name 
   Allows namechange command (with special condition that leverages UUID when available?)
4. No UUID Unchangable Name 
   Search by name, no worries
5. No UUID Changable Name 
   Allows namechange command