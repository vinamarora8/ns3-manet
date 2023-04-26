import numpy as np

def get_state_prop(line, tag):
    assert line.startswith(tag)
    return float(line.split(' ')[1])

def parse_states(state_fname):
    states = {}
    with open(state_fname, 'r') as file:
        lines = file.readlines()
        
        i = 0
        while i < len(lines):
            curr_time = int(get_state_prop(lines[i], 'TIME'))
            states[curr_time] = {}
            i+=1

            num_nodes = int(get_state_prop(lines[i], 'NUM_NODES'))
            states[curr_time]['positions'] = np.zeros((num_nodes, 3))
            i+=1

            num_sinks = int(get_state_prop(lines[i], 'NUM_SINKS'))
            states[curr_time]['sinks'] = np.arange(num_sinks)
            states[curr_time]['sources'] = np.arange(num_sinks) + num_sinks
            i+=1

            throughput = float(get_state_prop(lines[i], 'THROUGHPUT'))
            states[curr_time]['throughput'] = throughput
            i+=1

            assert lines[i].startswith('POSITIONS')
            i+=1

            for j in range(num_nodes):
                nodeid, posx, posy, posz = [x for x in lines[i].split(' ')]
                nodeid = int(nodeid)
                states[curr_time]['positions'][nodeid, 0] = float(posx)
                states[curr_time]['positions'][nodeid, 1] = float(posy)
                states[curr_time]['positions'][nodeid, 2] = float(posz)
                i+=1

    return states
