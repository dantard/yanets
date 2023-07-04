#!/usr/bin/env python

import argparse

import numpy

from CollisionDomain import CollisionDomain
from EventQueue import EventQueue
from Events import EventDataEnqueued, NodeEvent, CollisionDomainEvent
from Nodes import LoraNode, LoraGateway, LoraDevice
import yaml
from yaml.loader import SafeLoader
import csv


def main():
    parser = argparse.ArgumentParser(
        prog='Yanets',
        description='Yet Another NETwork Simulator',
        epilog='Have fun!')
    parser.add_argument('-f', '--config-file', type=str, default=None, help='Configuration file')
    parser.add_argument('-p', '--pose-file', type=str, default=None, help='Configuration file')

    args = parser.parse_args()

    # ### READ CONFIG FROM FILE ###
    if args.config_file is not None:
        try:
            with open(args.config_file) as f:
                config = yaml.load(f, Loader=SafeLoader)
        except FileNotFoundError:
            print("No config file found. Exiting.")
            exit(1)
    else:
        config = {}

    # ### READ POSES FROM FILE ###
    poses = []
    if args.pose_file is not None:
        try:
            with open(args.pose_file) as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',')
                for row in csv_reader:
                    x, y = row[0], row[1]
                    poses.append((x, y))
        except FileNotFoundError:
            print("No pose file found. Exiting.")
            exit(1)

    # Define varibale and their default values
    num_of_nodes = config.get('num_of_nodes', 5)
    num_of_gw = config.get('num_of_gateway', 2)
    payload = config.get('payload', 50)
    sim_lambda = config.get('lambda', 1)

    # ### MAIN Program ###
    numpy.random.seed(12)

    nodes = {}

    # Prepare Nodes
    event_queue = EventQueue()
    collision_domain = CollisionDomain(event_queue)

    # Create nodes
    for i in range(0, num_of_nodes):
        emitter = LoraNode(i, event_queue, collision_domain)
        emitter.set_pose(poses[i][0], poses[i][1]) if len(poses) > i else emitter.set_pose(i, i)
        nodes[emitter.id] = emitter

    # Create gateways
    for i in range(num_of_nodes, num_of_nodes + num_of_gw):
        gw = LoraGateway(i, event_queue, collision_domain)
        gw.set_pose(poses[i][0], poses[i][1]) if len(poses) > i else gw.set_pose(i, i)
        nodes[gw.id] = gw

    # Add nodes to collision domain
    collision_domain.set_nodes(nodes)

    # Create first event for each node
    for i in [n.id for n in nodes.values() if isinstance(n, LoraNode)]:
        ts = numpy.random.exponential(1000 / sim_lambda)
        new_event = EventDataEnqueued(ts, i)
        new_event.set_info({'source': i, 'payload': payload})
        event_queue.push(new_event)

    # Main event loop
    simulated_events = 0

    while event_queue.size() > 0 and simulated_events < 25:
        event = event_queue.pop()

        if isinstance(event, CollisionDomainEvent):
            collision_domain.process_event(event)

        elif isinstance(event, NodeEvent):
            node_id = event.get_node_id()
            nodes[node_id].process_event(event)

        # print("Processing event {} at ts:{}".format(type(event), event.get_ts()))
        print("{:21.12f} {:3d} {:30s} {} {}".format(event.get_ts(),
                                                    event.get_node_id(),
                                                    event.__class__.__name__,
                                                    [1 if c else 0 for c in collision_domain.get_transmitting()],
                                                    event.get_info()))
        simulated_events += 1

    for gw in nodes.values():
        print(gw.id, len(gw.get_received()))


if __name__ == "__main__":
    main()
