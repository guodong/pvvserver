import json
import os

TOPO_FILE = 'topo-add-rule.json'

if __name__ == '__main__':
    with open(TOPO_FILE, 'r') as f:
        data = f.read()
        topo = json.loads(data)
        for node in topo['nodes']:
            '''
            cmd = 'ovs-ofctl add-flow ' + node['name'] + ' priority=2,arp,arp_tpa=' + node['ip'] + ',actions=output:1'
            os.system(cmd)
            cmd = 'ovs-ofctl add-flow ' + node['name'] + ' priority=2,ip,nw_dst=' + node['ip'] + ',actions=output:1'
            os.system(cmd)

            cmd = 'ovs-ofctl add-flow ' + node['name'] + ' priority=1,arp,actions=flood'
            os.system(cmd)
            cmd = 'ovs-ofctl add-flow ' + node['name'] + ' priority=1,ip,actions=flood'
            os.system(cmd)
            '''
            cmd = 'ovs-ofctl add-flow ' + node['name'] + ' priority=2,in_port=1,actions=flood'
            os.system(cmd)
            cmd = 'ovs-ofctl add-flow ' + node['name'] + ' priority=1,udp,tp_dst=9999,actions=output:1'
            os.system(cmd)
