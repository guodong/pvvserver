import docker
import json
import os, time, signal

TOPO_FILE = 'bigtopo_docker.json'

client = docker.from_env()

containers = {}

class Network:
    def __init__(self):
        with open(TOPO_FILE, 'r') as f:
            data = f.read()
            self.topo = json.loads(data)

    def start(self):
        for node in self.topo['nodes']:
            print node['name']
            if node.has_key('type'):  # TODO: add type to all nodes
                container = client.containers.run('snlab/dovs-quagga', detach=True, name=node['name'], privileged=True, tty=True, network_mode='none')
            else:
                container = client.containers.run('snlab/dovs-quagga', detach=True, name=node['name'], privileged=True, tty=True)
            containers[node['name']] = container

        for link in self.topo['links']:
            srcArr = link['src'].split('.')
            dstArr = link['dst'].split('.')
            srcPid = client.containers.get(srcArr[0]).attrs['State']['Pid']
            dstPid = client.containers.get(dstArr[0]).attrs['State']['Pid']
            cmd = 'nsenter -t ' + str(srcPid) + ' -n ip link add ' + srcArr[1] + ' type veth peer name ' + dstArr[1] + ' netns ' + str(dstPid)
            os.system(cmd)

        # configure ovs
        for node in self.topo['nodes']:
            print 'configure ovs for ' + node['name']
            if node.has_key('type'):  # TODO: add type to all nodes
                continue
            c = client.containers.get(node['name'])
            c.exec_run('service openvswitch-switch start')
            c.exec_run('ovs-vsctl add-br s')
            c.exec_run('ovs-vsctl set-controller s tcp:127.0.0.1:6633')
            c.exec_run('ovs-vsctl set-fail-mode s secure')
            for port in node['ports']:
                internal_name = 'i' + port[1:]
                c.exec_run('ovs-vsctl add-port s ' + port)
                c.exec_run('ovs-vsctl add-port s ' + internal_name + ' -- set interface ' + internal_name + ' type=internal')

        # setup ip
        for node in self.topo['nodes']:
            print 'setup ip for ' + node['name']
            c = client.containers.get(node['name'])
            if not node.has_key('type'):
                for internal_port, ip in node['internal_ports'].items():
                    c.exec_run('ifconfig ' + internal_port + ' ' + ip)
            else:
                for port, ip in node['ports'].items():
                    c.exec_run('ifconfig ' + port + ' ' + ip)
                    c.exec_run('route add default gw ' + node['gw'])
                    c.exec_run('ifconfig ' + port + ' hw ether ' + node['hw'])

        # bring up external ports
        for node in self.topo['nodes']:
            if node.has_key('type'):
                continue
            c = client.containers.get(node['name'])
            for port in node['ports']:
                c.exec_run('ifconfig ' + port + ' 0.0.0.0')

        # configure quagga
        for node in self.topo['nodes']:
            print 'configure quagga for ' + node['name']
            if node.has_key('type'):
                continue
            c = client.containers.get(node['name'])
            cmd = 'bash -c "echo $\''
            for internal_port in node['internal_ports']:
                cmd += 'interface ' + internal_port + '\n'

            cmd += 'router ospf\n'
            for internal_port, ip in node['internal_ports'].items():
                cmd += ' network ' + ip[:-5] + '.0/24 area 0\n'

            cmd += '\' >> /etc/quagga/ospfd.conf"'
            c.exec_run(cmd)

            cmd = 'bash -c "echo $\''
            for internal_port, ip in node['internal_ports'].items():
                cmd += 'interface ' + internal_port + '\n ip address ' + ip + '\n'

            cmd += '\' >> /etc/quagga/zebra.conf"'
            c.exec_run(cmd)

        # set rules for ospf
        for node in self.topo['nodes']:
            print 'set rules for ospf for ' + node['name']
            if node.has_key('type'):
                continue
            c = client.containers.get(node['name'])
            c.exec_run('ovs-ofctl del-flows s')  # clear flows before setting
            i = 1
            for internal_port, ip in node['internal_ports'].items():
                # if not internal_port == 'i1':
                cmd = 'ovs-ofctl add-flow s in_port=' + str(i+1) + ',actions=output:' + str(i)
                c.exec_run(cmd)

                cmd = 'ovs-ofctl add-flow s ip,ip_proto=89,in_port=' + str(i) + ',actions=output:' + str(i+1)
                c.exec_run(cmd)
                if node['name'] == 'sea1' or node['name'] == 'ewr1':
                    idx = int(internal_port[1:])
                    if idx == 1:
                        cmd = 'ovs-ofctl add-flow s arp,arp_tpa=' + ip[:-3] + ',actions=output:2'  # dict iterator is not ordered!!!
                        c.exec_run(cmd)
                        cmd = 'ovs-ofctl add-flow s ip,nw_dst=' + ip[:-3] + ',actions=output:2'
                        c.exec_run(cmd)
                    else:
                        cmd = 'ovs-ofctl add-flow s arp,arp_tpa=' + ip[:-3] + ',actions=output:' + str(
                            (int(internal_port[1:]) - 3) * 2)  # dict iterator is not ordered!!!
                        c.exec_run(cmd)
                        cmd = 'ovs-ofctl add-flow s ip,nw_dst=' + ip[:-3] + ',actions=output:' + str(
                            (int(internal_port[1:]) - 3) * 2)
                        c.exec_run(cmd)
                else:
                    cmd = 'ovs-ofctl add-flow s arp,arp_tpa=' + ip[:-3] + ',actions=output:' + str(
                        (int(internal_port[1:]) - 4) * 2)  # dict iterator is not ordered!!!
                    c.exec_run(cmd)
                    cmd = 'ovs-ofctl add-flow s ip,nw_dst=' + ip[:-3] + ',actions=output:' + str(
                        (int(internal_port[1:]) - 4) * 2)
                    c.exec_run(cmd)
                i = i + 2

        # copy fpmserver into container
        for node in self.topo['nodes']:
            print 'copy multijet for ' + node['name']
            if node.has_key('type'):
                continue
            c = client.containers.get(node['name'])
            # os.system('docker cp fpmserver ' + node['name'] + ':/')
            # c.exec_run('/fpmserver/main.py', detach=True)
            os.system('docker cp /home/gd/PycharmProjects/multijet ' + node['name'] + ':/')
            c.exec_run('ryu-manager /multijet/multijet.py', detach=True)

        # add flow to resubmit to ospf tables
        for node in self.topo['nodes']:
            print 'add flow to resubmit to ospf tables for ' + node['name']
            if node.has_key('type'):
                continue
            c = client.containers.get(node['name'])
            c.exec_run('ovs-ofctl add-flow s priority=1,actions=resubmit\(,100\)')

        # start quagga
        for node in self.topo['nodes']:
            print 'start quagga for ' + node['name']
            if node.has_key('type'):
                continue
            c = client.containers.get(node['name'])
            c.exec_run('zebra -d -f /etc/quagga/zebra.conf --fpm_format protobuf')
            c.exec_run('ospfd -d -f /etc/quagga/ospfd.conf')

        print 'finished'

    def get_ofport_by_name(self, name):
        return


def signal_handler(sig, frame):
    print 'cleaning containers...'

    for name in containers:
        client.containers.get(name).remove(force=True)

    exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    network = Network()
    network.start()

    while True:
        time.sleep(1)