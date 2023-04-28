import os, sys
import numpy as np

def ip_to_node(ipstr):
    ipstr = ipstr.strip()
    b = [int(x) for x in ipstr.split('.')]

    if b[0] != 10:
        return False
    if b[1] != 1:
        return False
    if b[2] != 1:
        return False

    return b[3] - 1


def get_routing_overhead(trace_fname = 'manet-routing-compare.tr'):
    with open(trace_fname, 'r') as f:
        lines = f.readlines()

    protocols = ['aodv', 'olsr', 'dsdv']
    routing_name = None
    for p in protocols:
        if p in lines[0]:
            routing_name = p
            print(f'Detected routing protocol: {routing_name}')

    if routing_name is None:
        raise ValueError('Unknown routing protocol', lines[0], p)

    def is_tx_line(line):
        return 'State/Tx' in line

    def is_rx_line(line):
        return 'State/RxOk' in line

    def is_routing_line(line):
        return (routing_name in line)

    def is_payload_line(line):
        return 'Payload' in line

    # Parse routing lines
    routing_tx_lines = [x.strip() for x in lines if is_tx_line(x) and is_routing_line(x)]
    routing_info = []
    for l in routing_tx_lines:
        assert(l[0] == 't')
        time = float(l.split()[1])
        size = int(l.split('length: ')[1].strip().split()[0])
        nodeid = int(l.split('NodeList/')[1].split('/')[0])
        routing_info.append({
            'time': time,
            'nodeid': nodeid,
            'size': size,
        })

    def parse_payload_lines(lines):
        ans = []
        for l in lines:
            assert(l[0] == 't')
            time = float(l.split()[1])
            #seq = int(l.split('SeqNumber=')[1].split(')')[0])
            size, source_ip, _, dest_ip = l.split('length: ')[1].split(')')[0].split()
            size = int(size)
            nodeid = int(l.split('NodeList/')[1].split('/')[0])

            ans.append({
                'time': time,
                'nodeid': nodeid,
                'source_ip': source_ip,
                'source_nodeid': ip_to_node(source_ip),
                'dest_ip': dest_ip,
                'dest_nodeid': ip_to_node(dest_ip),
                'size': size,
            })
        return ans
        
    payload_tx_lines = [x.strip() for x in lines if is_tx_line(x) and is_payload_line(x)]
    payload_tx_info = parse_payload_lines(payload_tx_lines)
    payload_sources = [x for x in payload_tx_info if x['nodeid'] == x['source_nodeid']]

    min_time = min([x['time'] for x in payload_sources])
    routing_message_total_size = sum([x['size'] for x in routing_info if x['time'] > min_time])
    payload_sources_total_size = sum([x['size'] for x in payload_sources])
    routing_overhead = routing_message_total_size / payload_sources_total_size

    '''
    print('\n'.join(map(str, payload_sources)))
    print(payload_sources_total_size)
    print(routing_message_total_size)
    '''

    return routing_overhead

if __name__ == "__main__":
    print(get_routing_overhead())
