import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from parse_states import parse_states
from routing import Routing

state_fname = "manet-state.txt"
route_fname = "manet-rtable.txt"
xMax = 1000
yMax = xMax

states = parse_states(state_fname)

time_list = np.sort(list(states.keys()))
throughput_list = [states[t]['throughput'] for t in time_list]
    
x = []
y = []
fig, ax = plt.subplots()

def plot_line_bw_nodes(ax, pos, id0, id1, *args, **kwargs):
    ax.plot([pos[id0, 0], pos[id1, 0]],
            [pos[id0, 1], pos[id1, 1]],
            *args, **kwargs)

def plot_route(ax, pos, route, *args, **kwargs):
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

    cmap = plt.get_cmap('tab20', len(sources)+4)
    t = range(len(x[sinks]))

    ax.clear()
    ax.scatter(x, y, c='k', s=15)
    ax.scatter(x[sinks], y[sinks], c=cmap(t))
    ax.scatter(x[sources], y[sources], c=cmap(t))

    # Route lines
    r = Routing(num_nodes, route_fname, time=int(curr_time))
    for j in range(len(sources)):
        route = r.get_route(sources[j], sinks[j])
        if route is not None:
            plot_route(ax, positions, route, c=cmap(j))
        else:
            plot_line_bw_nodes(ax, positions, sources[j], sinks[j], 'k:', alpha=0.2)

    ax.set_xlim(0, xMax)
    ax.set_ylim(0, yMax)
    ax.set_title(f"$\\bf{{{r.type}}}$\nTime: {curr_time}s, Throughput: {states[curr_time]['throughput']:.2f}KBPS")

ani = FuncAnimation(fig, animate, frames=len(time_list), interval=100, repeat=False)
plt.show()
