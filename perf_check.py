from parse_fmon import run, get_metrics
import numpy as np
import matplotlib.pyplot as plt
import os
from parse_trace import get_routing_overhead

base_config = {
    'nWifi' : 20,
}

moving_param_name = 'nSinks'
moving_param_values = [2, 4, 6, 8, 10]

protocols = [1, 2, 3]
protocol_names = ['OLSR', 'AODV', 'DSDV']

metrics = []

for i, prot in enumerate(protocols):
    config = {'protocol': prot}
    config.update(base_config)

    metrics = metrics + [[]]

    for val in moving_param_values:
        config[moving_param_name] = val

        run(config)
        print(config)
        m = get_metrics('manet-routing-compare.flowmon', config['nSinks'])

        del m['overhead']
        m['Routing Overhead'] = get_routing_overhead(protocol_names[i])

        print(m)

        metrics[-1] += [m]

metric_names = [
    'Loss Rate',
    'Average Delay',
    'Routing Overhead',
    'Goodput' ,
]

os.system('mkdir -p plots/')
for metric in metric_names:
    for i, prot in enumerate(protocols):
        vals = [x[metric] for x in metrics[i]]
        plt.plot(moving_param_values, vals, label=protocol_names[i])
    plt.legend()
    plt.xlabel(moving_param_name)
    plt.ylabel(metric)
    plt.title(metric)
    plt.savefig(f'plots/{moving_param_name}_{metric}.png')
    plt.show()
