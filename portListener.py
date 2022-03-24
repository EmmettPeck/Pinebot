"""Listener processes to get docker log updates; Used by dockingPort"""

from multiprocessing import Process

# Builds queue between manager inside dockingPort and listener here

class Listener:
