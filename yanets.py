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
    parser.add_argument('-f', '--config-file', type=str, default=None, help='Configuration file', required=True)
    parser.add_argument('-p', '--pose-file', type=str, default="poses3.json", help='Configuration file', required=True)
    parser.add_argument('-r', '--random-seed', type=int, default=5, help='Random seed')

    args = parser.parse_args()

    # Read general config from file
    try:
        with open(args.config_file) as f:
            config = yaml.load(f, Loader=SafeLoader)
    except FileNotFoundError:
        print("No config file found. Exiting.")
        exit(1)

    global_conf = config.get("global")
    if global_conf is None:
        print("No global configuration found. Exiting.")
        exit(1)

    num_ed = global_conf.get("num_ed", 5)
    num_gw = global_conf.get("num_gw", 2)

    # Read position config from file
    try:
        with open(args.pose_file) as json_file:
            conf_data = json.load(json_file)
            num_of_nodes = len(conf_data)

    except FileNotFoundError:
        print("No pose file found. Exiting.")
        exit(1)

    # ### MAIN Program ###
    rng = numpy.random.default_rng(args.random_seed)
    Nodes.UserNode.set_rng(rng)

    # Prepare Nodes
    nodes = {}

    # Prepare objects
    event_queue = EventQueue()
    collision_domain = CollisionDomain(event_queue)

    # Create nodes
    ed_config = config.get("node", {})
    end_devices = config.get("nodes", [])
    for i in range(0, num_ed):
        emitter = CafcoNode(i, event_queue, collision_domain)
        emitter.update_config(ed_config)
        if len(end_devices) > i:
            emitter.update_config(end_devices[i])
        emitter.update_config(conf_data[i])
        nodes[emitter.id] = emitter

    # Create gateways
    gw_config = config.get("gateway", {})
    gateways = config.get("gateways",  [])
    for i in range(num_gw):
        gw = LoraGateway(num_ed + i, event_queue, collision_domain)
        gw.set_latlon(gateways[i]['latitude'], gateways[i]['longitude'])
        gw.update_config(gw_config)
        gw.update_config(gateways[i])
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
