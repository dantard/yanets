#!/usr/bin/env python

import argparse

import numpy

from CollisionDomain import CollisionDomain
from EventQueue import EventQueue
from Events import EventDataEnqueued, NodeEvent
from Nodes import LoraNode, LoraGateway
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
    num_of_gw = config.get('num_of_gateway', 1)
    payload = config.get('payload', 50)
    sim_lambda = config.get('lambda', 1)

    # ### MAIN Program ###
    gateways, emitters = [], []

    # Prepare Nodes
    event_queue = EventQueue()
    collision_domain = CollisionDomain()

    # Create nodes
    for i in range(num_of_nodes):
        emitter = LoraNode(i, event_queue, collision_domain)
        emitter.set_pose(poses[i][0], poses[i][1]) if len(poses) > i else emitter.set_pose(i,i)
        emitters.append(emitter)

    # Create gateways
    for i in range(num_of_gw):
        gw = LoraGateway(i, event_queue, collision_domain)
        gateways.append(gw)

    # Add nodes to collision domain
    collision_domain.append_nodes(emitters)
    collision_domain.append_nodes(gateways)

    # Create first event for each node
    for i in range(num_of_nodes):
        ts = numpy.random.exponential(1 / sim_lambda)
        event_queue.push(EventDataEnqueued(ts, i, payload))

    # Main event loop
    while event_queue.size() > 0:
        event = event_queue.pop()
        print("Processing event {} at ts:{}".format(type(event), event.get_ts()))
        if isinstance(event, NodeEvent):
            node = event.get_node()
            emitters[node].process_event(event)


if __name__ == "__main__":
    main()
