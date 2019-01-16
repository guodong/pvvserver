from mininet.node import Node, OVSBridge, OVSSwitch, RemoteController, OVSController
from mininet.link import TCLink
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel
import json

TOPO_FILE = 'topo-add-rule.json'

def network():
    net = Mininet()
    net.addController('c0', controller=RemoteController)
    with open(TOPO_FILE, 'r') as f:
        data = f.read()
        topo = json.loads(data)
        for node in topo['nodes']:
            print node['name']
            h = net.addHost(str('r' + node['name']), ip=node['ip'])  # must add str(), see https://github.com/mininet/mininet/issues/724
            s = net.addSwitch(str(node['name']), cls=OVSSwitch)
            net.addLink(h, s)

        for link in topo['links']:
            # net.addLink(net.getNodeByName(link['src']), net.getNodeByName(link['dst']), cls=TCLink, bw=100)
            net.addLink(net.getNodeByName(link['src']), net.getNodeByName(link['dst']))

        net.start()
        for host in net.hosts:
            host.cmd('ip route add default via 1.1.1.1')

        CLI(net)
        net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    network()

'''
class MyTopo(Topo):
    def __init__(self):
        super(MyTopo, self).__init__()
        self.nodes = {}
        with open('topo.json', 'r') as f:
            data = f.read()
            topo = json.loads(data)
            for node in topo['nodes']:
                r = self.addHost('r' + node['name'], ip=node['ip'])
                s = self.addSwitch(node['name'], cls=OVSSwitch)
                self.nodes.[node['name']] = s
                self.addLink(r, s)

            # for link in topo['links']:
            #     self.addLink(self.nodes[link['src']], self.nodes[link['dst']])


topos = {'topo':(lambda: MyTopo())}
'''
