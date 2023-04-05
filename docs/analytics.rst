.. _analytics:

Analytics
=========

Playtime Command
---------------------------------------------
    > Usage `\/playtime <playername> <optional-servername>`

Arguments
~~~~~~~~~
    * If a playername is not provided, attempts to get playtime for linked accounts to command sender.
    * If a discord account is mentioned, attempts to get playtime for that user's linked accounts.

.. warning::
    Unimplemented Case:
        * Without a server-name provided, the playtime total for each server the playername exists on is calculated. This currently only functions for :ref:`servers with account-ids<identifiers>`
        * Otherwise attempts searching servername for playername, totaling if present.

Playtime Calculation
~~~~~~~~~~~~~~~~~~~~
Queries server join/leave lists for provided player. Playtime is calculated in pairs by subtracting a join time from a leave time. The following cases are accounted for:
    * No joins (Returns 0)
    * First leave is before first join (Removes first leave)

To save compute space, pairs are indexed. New pairs are calculated and added to a running a total.
    * Most recent is a join (Player is online, displays off current time)
    * If there are no leaves or joins since the last calculation, returns the previous total.

Fixing logic is applied to leave/join lists on connect events:
    * is_recentest_join