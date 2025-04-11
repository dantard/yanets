#!/usr/bin/env python

import argparse
import json
import sys
from datetime import datetime

import numpy
import yaml
from yaml.loader import SafeLoader

import defaults
import rng
from Channel import Channel
from EventQueue import EventQueue
from Events import EventNewData, NodeEventWithFrame, ChannelEventWithFrame, EventLeaveChannel
from Nodes import LoraGateway, LoraEndDevice


def main():
    parser = argparse.ArgumentParser(
        prog='TAFCO Lora Simulator',
        description='TAFCO Lora Simulator')

    parser.add_argument('-f', '--config', type=str, default=None, help='Configuration file', required=True)
    parser.add_argument('-n', '--end-devices-config', type=str, help='End Devices configuration file', required=True)
    parser.add_argument('-r', '--random-seed', type=int, default=None, help='Random seed')

    args = parser.parse_args()

    # Read general config from YAML file
    try:
        with open(args.config) as f:
            yaml_config = yaml.load(f, Loader=SafeLoader)
    except FileNotFoundError:
        print("No config file found. Exiting.")
        exit(1)

    yaml_global_conf = yaml_config.get("global")
    if yaml_global_conf is None:
        print("No global configuration found. Exiting.")
        exit(1)

    yaml_channel_conf = yaml_config.get("channel_model")
    if yaml_channel_conf is None:
        print("No channel configuration found. Exiting.")
        exit(1)

    # Read end-devices specific configurations from JSON file
    try:
        with open(args.end_devices_config) as json_file:
            json_end_devices_conf = json.load(json_file)
    except FileNotFoundError:
        print("No End Devices config file found. Exiting.")
        exit(1)

    # Get number of nodes and gateways from the configuration files
    num_ed = len(json_end_devices_conf)
    num_gw = len(yaml_config.get("gateways", []))

    if num_ed == 0 or num_gw == 0:
        print("No nodes or gateways defined. Exiting.")
        exit(1)

    # MAIN Program

    # Get sim seed from command line or global config
    if args.random_seed is not None:
        seed = args.random_seed
    else:
        seed = yaml_global_conf.get("sim_seed", defaults.global_sim_seed)

    # Initialize random number generator
    rng.random_gen = numpy.random.default_rng(seed)

    # Prepare Nodes dictionary
    nodes = {}

    # Prepare EventQueue and Channel
    event_queue = EventQueue()
    channel = Channel(event_queue, yaml_channel_conf)

    # Create End Devices. These are assigned a node_id from 0 to num_ed -1
    # and are stored in the 'nodes' dictionary to ease the acces by node_id
    # This is internal and not related to the trackerid
    yaml_end_device_default = yaml_config.get("end_device_default", {})
    for i in range(0, num_ed):
        emitter = LoraEndDevice(i, event_queue, channel)

        # The configuration is updated from the config files: first the
        # 'end_device_default' section of the YAML file is processed
        # which is common for all the nodes and then the JSON file.
        emitter.update_config(yaml_end_device_default)
        emitter.update_config(json_end_devices_conf[i])

        nodes[emitter.id] = emitter

    # Create Gateway. These are assigned a node_id from num_ed to num_ed + num_gw -1
    # and are stored in the 'nodes' dictionary to ease the acces by node_id
    # This is internal and not related to the trackerid
    gateway_default = yaml_config.get("gateway_default", {})
    gateways = yaml_config.get("gateways", [])

    for i in range(num_gw):
        gw = LoraGateway(num_ed + i, event_queue, channel)

        # The configuration is updated from the YAML config file. First the
        # 'gateway_default' section is processed and then the 'gateways'
        # section. Notice that the trackerid is required in the 'gateways' section
        if not "trackerid" in gateways[i]:
            print("Field 'trackerid' is required in {} 'gateways' section file for node {}".format(args.config, i))
            exit(1)

        gw.update_config(gateway_default)
        gw.update_config(gateways[i])
        nodes[gw.id] = gw

    for n in nodes.values():
        print(n)

    # Add all the nodes to channel
    channel.set_nodes(nodes)

    # Create the first event for each end devices
    # (generation of the first packet) at time t_init
    for i in range(0, num_ed):
        ts = nodes[i].get_t_init()
        new_event = EventNewData(ts, nodes[i])
        event_queue.push(new_event)

    # Main event loop
    simulated_events = 0
    # Get the time stamp for the first event
    # to calculate the simulation duration
    sim_init = event_queue[0].get_ts()

    while event_queue.size() > 0:

        # Pop the first event from the queue
        # The queue is in ascending order of ts
        event = event_queue.pop(0)

        # Check if the simulation has been completed
        if event.get_ts() > sim_init + int(yaml_global_conf.get('sim_duration', defaults.global_sim_duration)):
            break

        # Process the event
        event.process()
        simulated_events += 1

        # Print events

        # Print nodes transmitting at this time
        for i, value in enumerate(channel.get_transmitting()):
            print(str(i) + " " if value else "  ", end="")

        # Prepare event details
        text = "{:6d}  {:14s} {:12.5f} {:>10}|{:>10}| {:18s} {}".format(
            simulated_events,
            datetime.fromtimestamp(event.get_ts()).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            event.get_ts() - sim_init,
            event.get_creator().get_trackerid() if type(event.get_creator()) is not Channel else "Channel ",
            event.get_handler().get_trackerid() if type(event.get_handler()) is not Channel else "Channel ",
            event.__class__.__name__,
            event.get_frame() if isinstance(event, (NodeEventWithFrame, ChannelEventWithFrame)) else ""
        )

        # Prepare frame details
        if isinstance(event, EventLeaveChannel):
            text += " {"
            for node, status in event.get_frame().get_receive_status().items():
                text += str(nodes.get(node).get_trackerid()) + ": " + str(status) + ", "
            text = text.rstrip(", ") + "}"

        # Print event
        print(text)

    # If the similator has finished, write the output
    with open(yaml_global_conf.get("sim_output", defaults.global_sim_output), "w") as f:
        json.dump(channel.get_output(), f, indent=4)


if __name__ == "__main__":
    main()
