#!/usr/bin/env python

from minknow_api import protocol_pb2 as protgrpc
from minknow_api.manager import Manager
import argparse
from pprint import pprint

"""Main entrypoint for list_sequencing_devices example"""
parser = argparse.ArgumentParser(
    description="List sequencing positions connected to a host."
)

parser.add_argument(
    "--host", default="localhost", help="Specify which host to connect to."
)
    
parser.add_argument(
    "--port", default=None, help="Specify which porer to connect to."
)

args = parser.parse_args()

# Construct a manager using the host + port provided.
manager = Manager(host=args.host, port=args.port, use_tls=False)

# Find a list of currently available sequencing positions.
positions = manager.flow_cell_positions()

# Print out available positions.
print("Available sequencing positions on %s:%s:" % (args.host, args.port))
for pos in positions:
    print("%s: %s" % (pos.name, pos.state))
    if pos.running:
        print("  secure: %s" % pos.description.rpc_ports.secure)
        print("  insecure: %s" % pos.description.rpc_ports.insecure)

position_connection = pos.connect()

print("Logging all run information to log/api_output_log.txt")

instance = position_connection.protocol.list_protocol_runs()
runs = instance.run_ids
for run in runs:
   info = position_connection.protocol.get_run_info(run_id=run)
   print(info, file=open("../log/api_output_log.txt", "a"))

print("...done...")
