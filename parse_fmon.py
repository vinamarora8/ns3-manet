import numpy as np
import xml.etree.ElementTree as ET
import pprint


def prep_stats(fname):
    tree = ET.parse(fname)

    root = tree.getroot()
    flowstats = None
    flowclassifier = None
    for child in root:
        if child.tag == "FlowStats":
            flowstats = child
        if child.tag == "Ipv4FlowClassifier":
            flowclassifier = child

    stats = {}
    for child in flowstats:
        attribs = child.attrib

        flowId = int(attribs['flowId'])
        del attribs['flowId']

        attribs['txPackets'] = int(attribs['txPackets'])
        attribs['rxPackets'] = int(attribs['rxPackets'])
        attribs['timesForwarded'] = int(attribs['timesForwarded'])
        attribs['delaySum'] = float(attribs['delaySum'][:-2]) * 1e-9
        stats[flowId] = attribs

    for child in flowclassifier:
        attribs = child.attrib
        flowId = int(attribs['flowId'])
        del attribs['flowId']
        stats[flowId].update(attribs)
    
    return stats


def print_stats(stats, cond=lambda v: True):
    for k, v in stats.items():
        if not cond(v):
            continue
        print(f"{k:<4} {v['sourceAddress']:<9}:{v['sourcePort']:>05} ({v['txPackets']:>3}) -> ({v['rxPackets']:>3}) {v['destinationAddress']:<9}:{v['destinationPort']:>05}", end="")
        print(f"\t {v['timesForwarded']:>3}")


def controlPackets(stats, cond=lambda v: True):
    ans = 0
    for k, v in stats.items():
        if cond(v):
            continue
        ans += v['rxPackets']
    return ans


def totRxPackets(stats, cond=lambda v: True):
    ans = 0
    for k, v in stats.items():
        ans += v['rxPackets']
    return ans


def controlOverhead(stats, cond=lambda v: True):
    return controlPackets(stats, cond) / totRxPackets(stats, cond)


def lossRate(stats, cond=lambda v: True):
    loss = 0
    totTxPackets = 0
    for k, v in stats.items():
        if not cond(v):
            continue
        loss += v['txPackets'] - v['rxPackets']
        totTxPackets += v['txPackets']
    return loss / totTxPackets


def averageDelay(stats, cond=lambda v: True):
    totRxPackets = 0
    totDelay = 0
    for k, v in stats.items():
        if not cond(v):
            continue
        totRxPackets += v['rxPackets']
        totDelay += v['delaySum']
    return totDelay / totRxPackets


if __name__ == "__main__":
    import sys, os
    fname = sys.argv[1]
    stats = prep_stats(fname)
    cond = lambda v: v['txPackets'] > 300
    print_stats(stats, cond)
    print('Loss Rate', lossRate(stats, cond))
    print('Average Delay(s)', averageDelay(stats, cond))
    print('Rx Packets', totRxPackets(stats, cond))
    print('Control Rx Packets', controlPackets(stats, cond))
    print('Control Overhead', controlOverhead(stats, cond))

    #pp = pprint.PrettyPrinter(indent=4)
    #pp.pprint(stats[1])
