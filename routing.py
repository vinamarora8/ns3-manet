import re
import traceback

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


    def __init__(self, numNodes, fname, time):
        """Read a complete routing table starting from line number `start`
        Length of the routing table is given by `numNodes`
        """
        self.numNodes = numNodes
        self.fname = fname
        self.routes = {}
        self.time = time

        with open(fname, 'r') as f:
            lines = [x.strip() for x in f.readlines()]

        i = 0
        started = lines[i].startswith('Node') and int(re.findall(r'[0-9]+', lines[i])[1]) == time
        while not started:
            i+=1
            started = lines[i].startswith('Node') and int(re.findall(r'[0-9]+', lines[i])[1]) == time

        nodesSeen = 0
        while i < len(lines) and nodesSeen < numNodes:
            assert lines[i].startswith('Node')
            nodeid = int(re.findall(r'[0-9]+', lines[i])[0])
            time_this = int(re.findall(r'[0-9]+', lines[i])[1])
            assert time_this == time, f'{nodeid}: {time_this} != {time}'
            nodesSeen += 1
            self.routes[nodeid] = {}
            i+=1

            while not lines[i].startswith('Destination'):
                i+=1
            i+=1

            while len(lines[i]) > 0:
                split = lines[i].split()
                i+=1
                
                if split[3] == 'IN_SEARCH':
                    continue

                if split[3] == 'DOWN':
                    continue

                dest = self.ip_to_node(split[0])
                gate = self.ip_to_node(split[1])
                hops = int(split[-1])
                #print(split, len(lines[i]), dest, gate)
                if dest is not False and gate is not False:
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
        src_orig = src
        dest_orig = dest
        route = [src]
        hops = self.routes[src][dest]['hops']
        while route[-1] != dest:
            if dest not in self.routes[src]:
                return None

            if hops <= 0:
                return None
            hops -= 1

            gate = self.routes[src][dest]['gate']
            route += [gate]
            src = gate
            dest = dest
        return route



if __name__ == "__main__":
    r = Routing(5, "manet-rtable.txt", time=110)
    print(r.routes)
    print(r.get_route(1, 0))

    r = Routing(5, "manet-rtable.txt", time=137)
    print(r.routes)
    print(r.get_route(1, 0))
