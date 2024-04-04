#!/usr/bin/env python

import argparse
import json
import sys

import numpy

import Nodes
from Channel import Channel
from EventQueue import EventQueue
from Events import EventNewData, NodeEvent, ChannelEvent, NodeEventWithFrame, ChannelEventWithFrame, EventLeaveChannel
from Frame import Frame
from Nodes import LoraNode, LoraGateway, LoraEndDevice
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
    parser.add_argument('-x', '--filter', type=int, default=-1, help='Visualize only event with this id')

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

    channel_conf = config.get("channel_model")
    if channel_conf is None:
        print("No channel configuration found. Exiting.")
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
    channel = Channel(event_queue, channel_conf)

    # Create nodes
    end_device_default = config.get("end_device_default", {})
    end_devices = config.get("end_devices", [])
    for i in range(0, num_ed):
        emitter = LoraEndDevice(i, event_queue, channel)
        emitter.update_config(end_device_default, False)
        if len(end_devices) > i:
            if not emitter.update_config(end_devices[i]):
                print("Field 'trackerid' is required in {} 'end_devices' section file".format(args.config))
                exit(1)
        if emitter.get_trackerid() is None:
            # Tracker id has not been filled yet, read directly from JSON
            # and assign values according to their positions in the list
            emitter.update_config(end_devices_conf[i])
        else:
            # Tracker id has been filled already so we have to look for
            # the corresponding node in the JSON file
            end_device_conf = next((item for item in end_devices_conf if item["trackerid"] == emitter.get_trackerid()), None)
            emitter.update_config(end_device_conf)

        nodes[emitter.id] = emitter


    # Create gateways
    gateway_default = config.get("gateway_default", {})
    gateways = config.get("gateways", [])
    print(gateways)
    for i in range(num_gw):
        gw = LoraGateway(num_ed + i, event_queue, channel)
        gw.update_config(gateway_default)
        if not gw.update_config(gateways[i]):
            print("Field 'trackerid' is required in {} 'gateways' section file".format(args.config))
            exit(1)
        nodes[gw.id] = gw

    # Add nodes to channel
    channel.set_nodes(nodes)


    for node in nodes.values():
        print(node)

    # Create first event for each node
    for i in [n.id for n in nodes.values() if isinstance(n, LoraEndDevice)]:
        ts = nodes[i].get_t_init()
        new_event = EventNewData(ts, nodes[i])
        event_queue.push(new_event)

    # Main event loop
    simulated_events = 0
    sim_init = event_queue[-1].get_ts()

    while event_queue.size() > 0:

        event = event_queue.pop()

        if event.get_ts() > sim_init + global_conf.get('sim_duration'):
            break

        event.process()
        simulated_events += 1

        # Print events

        # Filter to visualize only one node
        event_node_id = event.get_handler().get_node_id() if type(event.get_handler()) is not Channel else event.get_creator().get_node_id()
        if args.filter != -1 and event_node_id != args.filter:
            continue

        # Print nodes transmitting at this time
        for i, value in enumerate(channel.get_transmitting()):
            print(str(i) + " " if value else "  ", end="")

        # Prepare event details
        text = "{:6d} {:13.6f} {:>3}|{:>3}| {:18s} {}".format(
            simulated_events,
            event.get_ts(),
            event.get_creator().get_node_id() if type(event.get_creator()) is not Channel else "C",
            event.get_handler().get_node_id() if type(event.get_handler()) is not Channel else "C",
            event.__class__.__name__,
            event.get_frame() if isinstance(event, (NodeEventWithFrame, ChannelEventWithFrame)) else ""
        )

        # Prepare frame details
        if isinstance(event, EventLeaveChannel):
            text += " {"
            for node, reason in event.get_frame().get_receive_status().items():
                text += str(node) + ": " + str(reason) + ", "
            text = text.rstrip(", ") + "}"

        # Print event
        print(text)
    with open("output.json", "w") as f:
        json.dump(channel.get_output(), f)

    print(channel.get_output())


if __name__ == "__main__":
    main()
