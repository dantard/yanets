#!/usr/bin/env python

import argparse
import json
import sys

import numpy

import Nodes
from CollisionDomain import CollisionDomain
from EventQueue import EventQueue
from Events import EventDataEnqueued, NodeEvent, CollisionDomainEvent
from Frame import Frame
from Nodes import LoraNode, LoraGateway, CafcoNode, UserNode
import yaml
from yaml.loader import SafeLoader


def main():
    parser = argparse.ArgumentParser(
        prog='Yanets',
        description='Yet Another NETwork Simulator',
        epilog='Have fun!')
    parser.add_argument('-f', '--config-file', type=str, default=None, help='Configuration file')
    parser.add_argument('-p', '--pose-file', type=str, default="poses3.json", help='Configuration file')
    parser.add_argument('-r', '--random-seed', type=int, default=5, help='Random seed')

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

    num_of_gw = config.get('num_of_gateway', 2)

    if args.pose_file is not None:
        try:
            with open(args.pose_file) as json_file:
                conf_data = json.load(json_file)
                num_of_nodes = len(conf_data)

        except FileNotFoundError:
            print("No pose file found. Exiting.")
            exit(1)
    else:
        # Define varibale and their default values
        node_conf = {
            "_id": {
                "$oid": "64c634a0c6976e465b191e5d"
            },
            "trackerid": "bb000008",
            "longitude": "-2.6147869",
            "latitude": "42.9655609",
            "PHYPayload": "40080000bb000b02020d82e75f04b2a1b2878859af34612e",
            "content": "QAgAALsACwICDYLnXwSyobKHiFmvNGEu",
            "data": "bb1201422bdcbcc02758ab",
            "freq": [
                "868.5"
            ],
            "datr": [
                "SF7BW125"
            ],
            "codr": [
                "4/5"
            ]
        }
        num_of_nodes = config.get('num_of_nodes', 4)
        conf_data = []
        for i in range(num_of_nodes):
            conf_data.append(node_conf)

    # ### MAIN Program ###
    rng = numpy.random.default_rng(args.random_seed)
    Nodes.Node.set_rng(rng)
    #numpy.random.seed(config.get("random_seed"))

    nodes = {}

    # Prepare Nodes
    event_queue = EventQueue()
    collision_domain = CollisionDomain(event_queue)

    # Create nodes
    for i in range(0, num_of_nodes):
        emitter = CafcoNode(i, event_queue, collision_domain)
        emitter.set_config(conf_data[i])
        emitter.set_frame_generation_mode(Nodes.Node.MODE_RANDOM_UNIFORM, 100, 1000)
        nodes[emitter.id] = emitter
        # emitter.print()

    # Create gateways
    for i in range(num_of_nodes, num_of_nodes + num_of_gw):
        gw = LoraGateway(i, event_queue, collision_domain)
        gw.set_latlon(poses[i][0], poses[i][1]) if len(poses) > i else gw.set_latlon(i, i)
        nodes[gw.id] = gw

    # Add nodes to collision domain
    collision_domain.set_nodes(nodes)

    # Create first event for each node
    for i in [n.id for n in nodes.values() if isinstance(n, UserNode)]:
        ts = rng.exponential(1000 / 1)
        new_event = EventDataEnqueued(ts, Frame(nodes[i]))
        event_queue.push(new_event)

    # Main event loop
    simulated_events = 0
    while event_queue.size() > 0 and simulated_events < 1000:
        event = event_queue.pop()

        if isinstance(event, CollisionDomainEvent):
            collision_domain.process_event(event)
            obj = " "

        elif isinstance(event, NodeEvent):
            handler = event.get_handler()
            nodes[handler].process_event(event)
            obj = "G" if isinstance(nodes[handler], LoraGateway) else "N"
        else:
            obj = "?"

        for i, value in enumerate(collision_domain.get_transmitting()):
            print(str(i) + " " if value else "  ", end="")

        if event.get_handler() != 10:
            print("{:6d} {:21.12f} {} {:2d}|{:2d} {:30s} {:6d} {:4s} {} {:8.3f} {:8.3f} {}".format(simulated_events,
                event.get_ts(), obj,
                event.get_frame().get_source(), event.get_handler(),
                event.__class__.__name__, event.get_frame().get_serial(), event.get_frame().get_type(),
                [1 if c else 0 for c in collision_domain.get_transmitting()],
                event.get_frame().get_latlon()[0], event.get_frame().get_latlon()[1], event.get_frame().get_info()), list(event.get_frame().get_collisions()))
        simulated_events += 1



    #for gw in nodes.values():
    #    print(gw.id, len(gw.get_received()))


if __name__ == "__main__":
    main()
