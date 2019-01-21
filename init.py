import json
import os

TOPO_FILE = 'bigtopo.json'

if __name__ == '__main__':
    with open(TOPO_FILE, 'r') as f:
        data = f.read()
        topo = json.loads(data)
        for node in topo['nodes']:
            if node.has_key('type'):
                cmd = 'ovs-ofctl add-flow ' + node['name'] + ' priority=44444,in_port=3,udp,tp_src=9999,actions=flood'
                os.system(cmd)
                cmd = 'ovs-ofctl add-flow ' + node['name'] + ' priority=44444,udp,tp_dst=9999,actions=output:3'
                os.system(cmd)
            else:
                cmd = 'ovs-ofctl add-flow ' + node['name'] + ' priority=44444,in_port=1,udp,tp_src=9999,actions=flood'
                os.system(cmd)
                cmd = 'ovs-ofctl add-flow ' + node['name'] + ' priority=44444,udp,tp_dst=9999,actions=output:1'
                os.system(cmd)
