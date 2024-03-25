#!/usr/bin/env python

import argparse
import json
import sys

import numpy

import Nodes
from Channel import Channel
from EventQueue import EventQueue
from Events import EventNewData, NodeEvent, CollisionDomainEvent
from Frame import Frame
from Nodes import LoraNode, LoraGateway, CafcoNode, LoraEndDevice
import yaml
from yaml.loader import SafeLoader


def main():
    parser = argparse.ArgumentParser(
        prog='Yanets',
        description='Yet Another NETwork Simulator',
        epilog='Have fun!')
    parser.add_argument('-f', '--config', type=str, default=None, help='Configuration file', required=True)
    parser.add_argument('-n', '--end-devices-config', type=str, default="poses3.json", help='Configuration file', required=True)
    parser.add_argument('-r', '--random-seed', type=int, default=5, help='Random seed')

    args = parser.parse_args()

    # Read general config from file
    try:
        with open(args.config) as f:
            config = yaml.load(f, Loader=SafeLoader)
    except FileNotFoundError:
        print("No config file found. Exiting.")
        exit(1)

    global_conf = config.get("global")
    if global_conf is None:
        print("No global configuration found. Exiting.")
        exit(1)

    # Read position config from file
    try:
        with open(args.end_devices_config) as json_file:
            end_devices_conf = json.load(json_file)

    except FileNotFoundError:
        print("No nodes config file found. Exiting.")
        exit(1)

    num_ed = global_conf.get("num_ed", len(end_devices_conf))
    num_gw = global_conf.get("num_gw", len(config.get("gateways", [])))

    if num_ed == 0 or num_gw == 0:
        print("No nodes or gateways defined. Exiting.")
        exit(1)

    # ### MAIN Program ###
    rng = numpy.random.default_rng(args.random_seed)
    Nodes.LoraEndDevice.set_rng(rng)

    # Prepare Nodes
    nodes = {}

    # Prepare objects
    event_queue = EventQueue()
    channel = Channel(event_queue)

    # Create nodes
    end_device_default = config.get("end_device_default", {})
    end_devices = config.get("end_devices", [])
    for i in range(0, num_ed):
        emitter = LoraEndDevice(i, event_queue, channel)
        emitter.update_config(end_device_default)
        if len(end_devices) > i:
            emitter.update_config(end_devices[i])
        emitter.update_config(end_devices_conf[i])
        nodes[emitter.id] = emitter

    # Create gateways
    gateway_default = config.get("gateway_default", {})
    gateways = config.get("gateways",  [])
    for i in range(num_gw):
        gw = LoraGateway(num_ed + i, event_queue, channel)
        gw.update_config(gateway_default)
        gw.update_config(gateways[i])
        nodes[gw.id] = gw

    # Add nodes to channel
    channel.set_nodes(nodes)

    # Create first event for each node
    for i in [n.id for n in nodes.values() if isinstance(n, LoraEndDevice)]:
        ts = i
        new_event = EventNewData(ts, nodes[i])
        event_queue.push(new_event)

    # Main event loop
    simulated_events = 0
    while event_queue.size() > 0:

        event = event_queue.pop()

        if event.get_ts() > global_conf.get('sim_duration'):
            break

        if isinstance(event, CollisionDomainEvent):
            channel.process_event(event)
            obj = " "

        elif isinstance(event, NodeEvent):
            handler = event.get_handler()
            nodes[handler].process_event(event)
            obj = "G" if isinstance(nodes[handler], LoraGateway) else "N"
        else:
            obj = "?"

        for i, value in enumerate(channel.get_transmitting()):
            print(str(i) + " " if value else "  ", end="")

        if event.get_handler() != 10:
            print("{:6d} {:21.12f} {} {:2d}|{:2d} {:30s} {:6d} {:4s} {} {:8.3f} {:8.3f} {}".format(simulated_events,
                event.get_ts(), obj,
                event.get_frame().get_source(), event.get_handler(),
                event.__class__.__name__, event.get_frame().get_serial(), event.get_frame().get_type(),
                [1 if c else 0 for c in channel.get_transmitting()],
                event.get_frame().get_latlon()[0], event.get_frame().get_latlon()[1], event.get_frame().get_info()), list(event.get_frame().get_collisions()))
        simulated_events += 1



    #for gw in nodes.values():
    #    print(gw.id, len(gw.get_received()))


if __name__ == "__main__":
    main()
