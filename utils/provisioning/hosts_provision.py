import ast
import json
import os
import sys
from typing import List
from collections import namedtuple
from json import JSONEncoder


class Microservice:
    def __init__(
        self,
        microserviceID: str,
        microservice_name: str,
        microservice_namespace: str,
        virtualization: str,
        cmd: List[str],
        expected_output: str,
        memory: int,
        vcpus: int,
        vgpus: int,
        vtpus: int,
        bandwidth_in: int,
        bandwidth_out: int,
        storage: int,
        code: str,
        state: str,
        port: str,
        added_files: List[str],
    ):
        self.microserviceID = microserviceID
        self.microservice_name = microservice_name
        self.microservice_namespace = microservice_namespace
        self.virtualization = virtualization
        self.cmd = cmd
        self.expected_output = expected_output
        self.memory = memory
        self.vcpus = vcpus
        self.vgpus = vgpus
        self.vtpus = vtpus
        self.bandwidth_in = bandwidth_in
        self.bandwidth_out = bandwidth_out
        self.storage = storage
        self.code = code
        self.state = state
        self.port = port
        self.added_files = added_files


class Application:
    def __init__(
        self,
        applicationID: str,
        application_name: str,
        application_namespace: str,
        application_desc: str,
        microservices: List[Microservice],
    ):
        self.applicationID = applicationID
        self.application_name = application_name
        self.application_namespace = application_namespace
        self.application_desc = application_desc
        self.microservices = microservices


class SLADescriptor:
    def __init__(
        self, sla_version: str, customerID: str, applications: List[Application]
    ):
        self.sla_version = sla_version
        self.customerID = customerID
        self.applications = applications


class Cluster:
    def __init__(
        self, cluster_number: int, workers_number: int, sla_descriptor: SLADescriptor
    ):
        self.cluster_number = cluster_number
        self.workers_number = workers_number
        self.sla_descriptor = sla_descriptor


class TopologyDescriptor:
    def __init__(self, onedoc: bool, mdoc: bool, cluster_list: List[Cluster]):
        self.onedoc = onedoc
        self.mdoc = mdoc
        self.cluster_list = cluster_list


class TopologyEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__


def customTopologyDecoder(topologyDict):
    return namedtuple("TopologyDescriptor", topologyDict.keys())(*topologyDict.values())


def precheck_hosts_availability(topology):
    descriptor = topology.topology_descriptor
    total_required_hosts = 0

    if descriptor.onedoc:
        return 1

    if descriptor.mdoc:
        total_required_hosts = 1
        if descriptor.cluster_list:
            total_required_hosts += descriptor.cluster_list[0].workers_number

    else:
        total_required_hosts = (
            len(descriptor.cluster_list)
            + sum(cluster.workers_number for cluster in descriptor.cluster_list)
            + 1
        )

    return total_required_hosts


def check_list(param_str: str):
    """Check if the string is a valid list."""
    try:
        converted_list = ast.literal_eval(param_str)
        if not isinstance(converted_list, list):
            print(f"Error: {param_str} parameter is not a list")
            return
        else:
            return converted_list
    except (SyntaxError, ValueError) as e:
        print(f"Error converting {param_str} string to list: {e}")
        return


def add_dispatch_group(topology_filename, topologyObj, dispatch_dict, reserved_hosts):

    if topologyObj.topology_descriptor.onedoc:
        item = {
            "topology_filename": topology_filename,
            "group_1doc": reserved_hosts,
        }
        dispatch_dict["onedoc"].append(item)
    elif topologyObj.topology_descriptor.mdoc:
        item = {
            "topology_filename": topology_filename,
            "group_mdoc_root": [reserved_hosts[0]],
            "group_mdoc_workers": reserved_hosts[1:],
        }
        dispatch_dict["mdoc"].append(item)

    else:
        cluster_nodes = len(topologyObj.topology_descriptor.cluster_list)

        item = {
            "topology_filename": topology_filename,
            "group_mdnc_root": [reserved_hosts[0]],
            "group_mdnc_clusters": reserved_hosts[1 : cluster_nodes + 1],
            "group_mdnc_workers": reserved_hosts[cluster_nodes + 1 :],
        }
        dispatch_dict["mdnc"].append(item)

    dispatch_dict["reserved_hosts"] = list(
        set(dispatch_dict["reserved_hosts"] + reserved_hosts)
    )


def main():

    if len(sys.argv) != 3:
        print("Error: Expected exactly four command-line arguments.")
        return

    # Parse command-line arguments
    topologies_dir, available_hosts = sys.argv[1:3]

    available_hosts = check_list(available_hosts)

    # Read all the json files in the folder `topologies_folder`
    json_files = [
        pos_json
        for pos_json in os.listdir(topologies_dir)
        if pos_json.endswith(".json")
    ]

    total_available_hosts = len(available_hosts)

    dispatch_dict = {"reserved_hosts": [], "onedoc": [], "mdoc": [], "mdnc": []}

    for topology_filename in json_files:
        try:
            file_path = topologies_dir + "/" + topology_filename
            with open(file_path, "r") as f:
                topologyObj = json.load(f, object_hook=customTopologyDecoder)

                total_required_hosts = precheck_hosts_availability(topologyObj)

                if total_required_hosts <= total_available_hosts:
                    # print(f"Available hosts: {available_hosts}")

                    reserved_hosts = available_hosts[:total_required_hosts]
                    # print(f"Reserved hosts: {reserved_hosts}")
                    # available_hosts = available_hosts[total_required_hosts:]
                    add_dispatch_group(
                        topology_filename, topologyObj, dispatch_dict, reserved_hosts
                    )

                    # total_available_hosts -= total_required_hosts
        except Exception as e:
            print(f"Error: {e}")

    # Save dispatch_dict to a JSON file
    with open(topologies_dir + "/dispatch.json", "w") as f:
        try:
            # Check if dispatch_dict['onedoc'] is empty
            no_dispatch = all(len(value) == 0 for value in dispatch_dict.values())
            if no_dispatch:
                json.dump({}, f)
            else:
                dispatch_dict["reserved_hosts"] = list(
                    set(dispatch_dict["reserved_hosts"])
                )
                json.dump(dispatch_dict, f, cls=TopologyEncoder, indent=4)
                print(dispatch_dict)
        finally:
            f.close()

    # print(json_files)

    # print(available_hosts)


if __name__ == "__main__":
    main()
