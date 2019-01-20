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
            c = client.containers.get(node['name'])
            c.exec_run('service openvswitch-switch start')
            c.exec_run('ovs-vsctl add-br s')
            for port in node['ports']:
                internal_name = 'i' + port[1:]
                c.exec_run('ovs-vsctl add-port s ' + port)
                c.exec_run('ovs-vsctl add-port s ' + internal_name + ' -- set interface ' + internal_name + ' type=internal')

        # setup ip
        for node in self.topo['nodes']:
            c = client.containers.get(node['name'])
            for internal_port, ip in node['internal_ports'].items():
                c.exec_run('ifconfig ' + internal_port + ' ' + ip)

        # bring up external ports
        for node in self.topo['nodes']:
            c = client.containers.get(node['name'])
            for port in node['ports']:
                c.exec_run('ifconfig ' + port + ' 0.0.0.0')

        # configure quagga
        for node in self.topo['nodes']:
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
            c = client.containers.get(node['name'])
            c.exec_run('ovs-ofctl del-flows s')  # clear flows before setting
            i = 1
            for internal_port, ip in node['internal_ports'].items():
                cmd = 'ovs-ofctl add-flow s ip,ip_proto=89,in_port=' + str(i) + ',actions=output:' + str(i+1)
                c.exec_run(cmd)
                cmd = 'ovs-ofctl add-flow s arp,arp_tpa=' + ip[:-3] + ',actions=output:' + str((int(internal_port[1:]) - 4) * 2)  # dict iterator is not ordered!!!
                c.exec_run(cmd)
                # cmd = 'ovs-ofctl add-flow s ip,nw_dst=' + ip[:-3] + ',actions=output:' + str(i+1)
                # c.exec_run(cmd)
                cmd = 'ovs-ofctl add-flow s in_port=' + str(i+1) + ',actions=output:' + str(i)
                c.exec_run(cmd)
                i = i + 2

        # start quagga
        print 'starting quagga'
        for node in self.topo['nodes']:
            c = client.containers.get(node['name'])
            c.exec_run('zebra -d -f /etc/quagga/zebra.conf --fpm_format protobuf')
            c.exec_run('ospfd -d -f /etc/quagga/ospfd.conf')



    def get_node_by_name(self, name):
        for node in self.topo['nodes']:
            if node['name'] == name:
                return node

        return None


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