from parse_fmon import run, get_metrics
import numpy as np
import matplotlib.pyplot as plt
import os

# Config
protocols = [1, 2, 3]
protocol_names = ['OLSR', 'AODV', 'DSDV']

'''
base_config = {
    'nWifi' : 20,
}

moving_param_name = 'nSinks'
moving_param_values = [2, 4, 6, 8, 10]
'''


'''
base_config = {
    'nWifi' : 50,
    'pauseTime': 2, # Max time is 2
    #'nodeSpeed': 20, # Range is .5x - x 
    'packetSize':64, 
    'nSinks':15
}
moving_param_name = 'nodeSpeed'
moving_param_values = [2,  8 , 12 ,  18, 24  ]
'''

'''
base_config = {
    'nWifi' : 50,
    #'pauseTime': 2, # Max time is 2
    'nodeSpeed': 20, # Range is .5x - x 
    'packetSize':64, 
    'nSinks':15
}
moving_param_name = 'pauseTime'
moving_param_values = [2,  4  , 6 , 8 , 10 ] #128 , 256 ,  512, 1024  ]
'''

'''
base_config = {
    'nWifi' : 50,
    'pauseTime': 2, # Max time is 2
    'nodeSpeed': 20, # Range is .5x - x 
    #'packetSize':64, 
    'nSinks':15
}
moving_param_name = 'packetSize'
moving_param_values = [64, 128, 256, 512, 1024] #128 , 256 ,  512, 1024  ]
'''

base_config = {
    #'nWifi' : 50,
    'pauseTime': 2, # Max time is 2
    'nodeSpeed': 0, # Range is .5x - x 
    'packetSize':64, 
    'nSinks':10
}
moving_param_name = 'nWifi'
moving_param_values = [20, 30, 40, 50] #128 , 256 ,  512, 1024  ]

'''
base_config = {
    'nWifi' : 30,
    'pauseTime': 2, # Max time is 2
    'nodeSpeed': 20, # Range is .5x - x 
    'packetSize':64, 
    #'nSinks':5
}
moving_param_name = 'nSinks'
moving_param_values = [2, 4, 6, 8, 10] #128 , 256 ,  512, 1024  ]
'''

averages = 1


# Get metrics
config_count = len(moving_param_values)*len(protocols)
metrics = []
for i, prot in enumerate(protocols):
    config = {'protocol': prot}
    config.update(base_config)

    metrics = metrics + [[]]

    for j, val in enumerate(moving_param_values):
        config[moving_param_name] = val
        #config['nSinks'] = val // 4

        # Average
        m = [] # List of metrics over multiple runs
        print()
        print(f'CONFIG: {j + 1 + i*len(moving_param_values)}/{config_count}')
        print(config)
        for n in range(averages):
            print()
            print(f'{n+1}/{averages}:')
            config['seed'] = n * 1234122 + 23
            run(config)
            m.append(get_metrics('manet-routing-compare.flowmon', config['nSinks']))
            print(m[-1])

        m_avg = m[0].copy()

        for k in m_avg:
            m_avg[k] = (np.mean([x[k] for x in m]), np.std([x[k] for x in m]) / np.sqrt(averages))

        print("Averaged")
        print(m_avg)
        metrics[-1] += [m_avg]

# Plot
metric_names = metrics[0][0].keys()
os.system('mkdir -p plots/')
for metric in metric_names:
    for i, prot in enumerate(protocols):
        vals = [x[metric][0] for x in metrics[i]]
        std = [x[metric][1] for x in metrics[i]]
        if averages > 1:
            plt.errorbar(moving_param_values, vals, std, capsize=3.0, label=protocol_names[i])
        else:
            plt.plot(moving_param_values, vals, label=protocol_names[i])
    plt.legend()
    plt.xlabel(moving_param_name)
    plt.ylabel(metric)
    plt.title(f'{metric} vs {moving_param_name}')
    plt.grid()
    #plt.xscale('log', base=2)

    plt.savefig(f'plots/{moving_param_name}_{metric}.png')
    plt.show()
