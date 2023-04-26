import numpy as np
import re

class Routing():

    def ip_to_node(self, ipstr):
        b = [int(x) for x in ipstr.split('.')]

        if b[0] != 10:
            return False
        if b[1] != 1:
            return False
        if b[2] != 1:
            return False
        if b[3] > self.numNodes + 1:
            return False

        return b[3] - 1


    def __init__(self, numNodes, fname, start=0):
        """Read a complete routing table starting from line number `start`
        Length of the routing table is given by `numNodes`
        """
        self.numNodes = numNodes
        self.fname = fname
        self.routes = {}

        with open(fname, 'r') as f:
            lines = [x.strip() for x in f.readlines()]

        i = start
        nodesSeen = 0
        while i < len(lines) and nodesSeen < numNodes:
            assert lines[i].startswith('Node')
            nodeid = int(re.findall(r'[0-9]+', lines[i])[0])
            nodesSeen += 1
            self.routes[nodeid] = {}
            print(nodeid)
            i+=1

            while not lines[i].startswith('Destination'):
                i+=1
            i+=1

            while len(lines[i]) > 0:
                split = lines[i].split()
                i+=1
                
                if split[3] == 'IN_SEARCH':
                    continue

                dest = self.ip_to_node(split[0])
                gate = self.ip_to_node(split[1])
                hops = int(split[-1])
                #print(split, len(lines[i]), dest, gate)
                if dest:
                    self.routes[nodeid][dest] = {
                        'path':[dest],
                        'gate':gate,
                        'hops':hops
                    }

            while i < len(lines) and len(lines[i]) == 0:
                i+=1

        self.lastline = i

    def get_route(self, src, dest):
        if dest not in self.routes[src]:
            return None
        route = [src]
        for i in range(self.routes[src][dest]['hops']):
            gate = self.routes[src][dest]['gate']
            route += [gate]
            src = gate
            dest = dest
        return route



if __name__ == "__main__":
    r = Routing(10, "rtable.txt", start=0)
    print(r.lastline)
    print(r.routes)
    print(r.get_route(0, 2))
    print(r.get_route(5, 2))
    print(r.get_route(2, 0))

    r = Routing(10, "rtable.txt", start=r.lastline)
    print(r.lastline)
    print(r.routes)
    print(r.get_route(0, 2))
    print(r.get_route(5, 2))
    print(r.get_route(2, 0))
