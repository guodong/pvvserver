import sys
import time
import os, signal
from node import Node

# TOPO_FILE = 'topo-add-rule.json'
TOPO_FILE = 'bigtopo.json'



if __name__ == '__main__':
    print os.getpid()

    node = Node(TOPO_FILE)
    signal.signal(signal.SIGIO, node.init)
    if len(sys.argv) > 1:
        node.init()
    else:
        node.bootstrap()
    while True:
        time.sleep(1)
