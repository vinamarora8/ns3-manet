from random import randint
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from typing import Dict, Any
from matplotlib.colors import ListedColormap
from routing import Routing

fname = "manet-state.txt"
route_fname = "manet-rtable.txt"
states = {}
with open(fname, 'r') as file:
    lines = file.readlines()
    
    i = 0
    while i < len(lines):
        assert lines[i].startswith('TIME')
        curr_time = float(lines[i].split(' ')[1])
        states[curr_time] = {}
        i+=1

        assert lines[i].startswith('NUM_NODES')
        num_nodes = int(lines[i].split(' ')[1])
        states[curr_time]['positions'] = np.zeros((num_nodes, 3))
        i+=1

        assert lines[i].startswith('NUM_SINKS')
        num_sinks = int(lines[i].split(' ')[1])
        states[curr_time]['sinks'] = np.arange(num_sinks)
        states[curr_time]['sources'] = np.arange(num_sinks) + num_sinks
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

time_list = np.sort(list(states.keys()))
    
x = []
y = []
fig, ax = plt.subplots()

def plot_line_bw_nodes(ax, pos, id0, id1, *args, **kwargs):
    ax.plot([pos[id0, 0], pos[id1, 0]],
            [pos[id0, 1], pos[id1, 1]],
            *args, **kwargs)

def plot_route(ax, pos, route, *args, **kwargs):
    if route is None:
        return
    
    assert len(route) >= 2
    for i in range(len(route) - 1):
        plot_line_bw_nodes(ax, pos, route[i], route[i+1], *args, **kwargs)

def animate(i):
    global x, y, ax

    curr_time = time_list[i]
    positions = states[curr_time]['positions']
    num_nodes = len(positions)
    sinks = states[curr_time]['sinks']
    sources = states[curr_time]['sources']
    assert len(sinks) == len(sources)

    x = positions[:, 0]
    y = positions[:, 1]

    ax.clear()
    ax.scatter(x, y)
    ax.scatter(x[sinks], y[sinks], label="Sinks")
    ax.scatter(x[sources], y[sources], label="Sources")


    # Route lines
    r = Routing(num_nodes, route_fname, time=int(curr_time))
    cmap = plt.get_cmap('hsv', len(sources)+4)
    for j in range(len(sources)):
        route = r.get_route(sources[j], sinks[j])
        if route is not None:
            plot_route(ax, positions, route, c=cmap(j))
        else:
            plot_line_bw_nodes(ax, positions, sources[j], sinks[j], 'k:', alpha=0.2)


    ax.set_xlim(0, 300)
    ax.set_ylim(0, 1500)
    ax.set_title(f"Time: {curr_time}s")
    ax.legend(loc='upper right')

ani = FuncAnimation(fig, animate, frames=len(time_list), interval=100, repeat=False)
plt.show()
