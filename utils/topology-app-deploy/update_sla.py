import bisect
import sys
import json
import ast
from icmplib import ping
import requests
import aiohttp
import asyncio


def validate_topology(data):
    """Validate the topology data structure."""
    # TODO: Add more validation checks
    return isinstance(data, dict)


def post_request_sync(url, json_body):
    """Post JSON data to the specified endpoint using the provided token."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {authToken}",
    }

    try:
        response = requests.post(url, headers=headers, json=json_body)
        if response.status_code in (200, 201):
            return response.status_code, response.json()
        else:
            return response.status_code, response.text
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")


def get_request_sync(url):
    """Get JSON data from the specified endpoint using the provided token."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {authToken}",
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code in (200, 201):
            return response.status_code, response.json()
        else:
            return response.status_code, response.text
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None, str(e)


async def post_request(url, json_body):
    """Asynchronously post JSON data to the specified endpoint using the provided token."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {authToken}",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=json_body) as response:
                if response.status in (200, 201):
                    return response.status, await response.json()
                else:
                    return response.status, await response.text()
    except aiohttp.ClientError as e:
        print(f"An error occurred: {e}")
        return None, str(e)


async def get_request(url):
    """Asynchronously get JSON data from the specified endpoint using the provided token."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {authToken}",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status in (200, 201):
                    return response.status, await response.json()
                else:
                    return response.status, await response.text()
    except aiohttp.ClientError as e:
        print(f"An error occurred: {e}")
        return None, str(e)


def authenticate(
    SYSTEM_MANAGER_URL="localhost", username="Admin", password="Admin", organization=""
):
    """Authenticate with the server and return a token."""
    login_url = f"http://{SYSTEM_MANAGER_URL}:10000/api/auth/login"
    payload = {"username": username, "password": password, "organization": organization}

    try:
        response = requests.post(login_url, json=payload)
        if response.status_code == 200:
            token = response.json().get("token")
            if token:
                return token
            else:
                print("Authentication successful, but no token found in the response.")
        else:
            print(f"Failed to authenticate: {response.status_code} - {response.text}")
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
    return None


def is_reachable(SYSTEM_MANAGER_URL):
    """Check if a host is reachable by sending a ping request."""
    host = ping(SYSTEM_MANAGER_URL, count=1, interval=0.2)
    return host.packets_sent == host.packets_received


def constrained_already_specified(constraints: list):
    for constraint in constraints:
        if constraint.get("type") == "direct" and (
            "node" in constraint or "cluster" in constraint
        ):
            return True
        return False


def update_topology(clusters, workers, cluster_names, deploy_mode):
    """Update the topology with the available worker nodes."""

    log_verifier = {}

    for cluster in clusters:
        number_of_nodes = cluster.get("workers_number", 0)
        assigned_workers = workers[:number_of_nodes]
        del workers[:number_of_nodes]

        if cluster_names:
            cluster_suffix = cluster_names.pop(0)

        used_workers = []
        for app in cluster["sla_descriptor"]["applications"]:

            application_prefix = (
                app["application_name"] + "." + app["application_namespace"]
            )
            for service_index, service in enumerate(app["microservices"]):
                if assigned_workers:
                    assigned_worker = assigned_workers.pop(0)
                    used_workers.append(assigned_worker)
                else:
                    assigned_worker = used_workers[service_index % len(used_workers)]

                print(service)
                if "expected_output" in service:
                    expected_output = service["expected_output"]
                    microservice_suffix = (
                        service["microservice_name"]
                        + "."
                        + service["microservice_namespace"]
                    )
                    identifier = application_prefix + "." + microservice_suffix
                    log_verifier[identifier] = expected_output
                    print(f"Expected output {expected_output} for service {identifier}")
                    service.pop("expected_output")

                if deploy_mode == "rc" or deploy_mode == "full":

                    if (
                        "constraints" not in service
                        or not constrained_already_specified(service["constraints"])
                    ):
                        service["constraints"] = [
                            {
                                "type": "direct",
                                "node": assigned_worker,
                                "cluster": "CL" + cluster_suffix,
                            }
                        ]
    return log_verifier
    # with open("/tmp/log_verifier.json", "w") as f:
    #    json.dump(log_verifier, f, indent=4)


def check_correspondence(json_data, workers, cluster_names, deploy_mode):
    """Check if the number of workers matches the required nodes and update the topology."""
    clusters = json_data.get("topology_descriptor", {}).get("cluster_list", [])
    total_nodes = sum(cluster.get("workers_number", 0) for cluster in clusters)

    if len(workers) < total_nodes:
        print("Insufficient worker nodes.")
        return False

    expected_app_output = update_topology(clusters, workers, cluster_names, deploy_mode)
    return json_data, expected_app_output


async def deploy_application(updated_sla: dict):
    endpoint = f"http://{SYSTEM_MANAGER_URL}:10000/api/application/"
    topology = updated_sla.get("topology_descriptor", {})
    clusters = topology.get("cluster_list", [])
    success = {}
    failed = {}
    deployed_apps = []

    for cluster in clusters:
        sla_descriptor = cluster.get("sla_descriptor", {})
        status_code, body = await post_request(endpoint, sla_descriptor)

        if status_code in (200, 201):

            success[cluster["cluster_number"]] = []
            failed[cluster["cluster_number"]] = []
            if isinstance(body, (str, bytes, bytearray)):
                body = json.loads(body)
            for app in body:
                if app["applicationID"] not in deployed_apps:
                    deployed_apps.append(app["applicationID"])
                    if isinstance(app, dict):
                        microservices = app.get("microservices", [])
                        for microservice_id in microservices:
                            instance_endpoint = f"http://{SYSTEM_MANAGER_URL}:10000/api/service/{microservice_id}/instance"
                            status_code, instance_body = await post_request(
                                instance_endpoint, {}
                            )
                            if status_code in (200, 201):
                                success[cluster["cluster_number"]].append(
                                    microservice_id
                                )
                            else:
                                failed[cluster["cluster_number"]].append(
                                    microservice_id
                                )
                    else:
                        print(f"Application is not a dict type: {app}")
        else:
            failed[cluster["cluster_number"]] = (
                f"SLA_POST_FAILED_{status_code}_{instance_body}"
            )

    return success, failed


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


"""

{
    "running_processes": {
        "192.168.1.2": {
                    "newapp.test2.service1.test1": "Service 1 is running"
                    "newapp.test2.service2.test2.instance.0": "Service 2 is running",
                    },
        "192.168.1.3": {
                    "clientsrvr1.test1.curl.test1": "HTTP 404",
                    "clientsrvr1.test1.nginx.test1". "HTTP 303",
                        }
    },
    "failed_process": {
        "MicroserviceID_1": "FAILED",
    } 
}

"""


def find_matching_prefix(process, sorted_prefixes):
    idx = bisect.bisect_left(sorted_prefixes, process)

    if idx < len(sorted_prefixes) and process.startswith(sorted_prefixes[idx]):
        return sorted_prefixes[idx]

    if idx > 0 and process.startswith(sorted_prefixes[idx - 1]):
        return sorted_prefixes[idx - 1]

    return None


import json


async def application_healthcheck(
    system_manager_url, deployed_apps, worker_list, expected_outputs
):
    running_statuses = {}
    failed_statuses = {}
    services_unified = []

    # Collect all services from deployed_apps
    for app_list in deployed_apps.values():
        services_unified.extend(app_list)

    # Sort process prefixes for searching
    sorted_prefixes = sorted(expected_outputs.keys())

    # Fetch the status from the system manager
    request_status, request_body = await get_request(
        url=f"http://{system_manager_url}:10000/api/services/"
    )

    if request_status in {200, 201}:
        request_body = json.loads(request_body)

        if request_body:
            for service in request_body:
                microservice_id = service.get("microserviceID")
                if microservice_id in services_unified:
                    for instance in service.get("instance_list", []):
                        process_name = f"{service['job_name']}.instance.{instance.get('instance_number')}"

                        if instance.get("status") == "RUNNING":
                            host = instance.get("publicip")

                            process_prefix = find_matching_prefix(
                                process_name, sorted_prefixes
                            )

                            if process_prefix:
                                expected_output = expected_outputs[process_prefix]

                                if host not in running_statuses:
                                    running_statuses[host] = {}

                                running_statuses[host][process_name] = expected_output

                        else:
                            failed_statuses[microservice_id] = (
                                f"{process_name}_{instance.get('status')}"
                            )

    return running_statuses, failed_statuses


async def main_async():
    if len(sys.argv) != 5:
        print("Error: Expected exactly four command-line arguments.")
        return

    # Parse command-line arguments
    json_file, worker_str, inventory_str, root_str = sys.argv[1:5]

    # Read the topology descriptor temp JSON file
    try:
        with open(json_file, "r") as f:
            json_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading JSON file: {e}")
        return

    # Convert the string parameters to lists
    worker_list = check_list(worker_str)
    root_group = check_list(root_str)
    cluster_names = check_list(inventory_str)

    if validate_topology(json_data):
        onedoc_enabled = json_data.get("topology_descriptor", {}).get("onedoc", False)
        rc_enabled = json_data.get("topology_descriptor", {}).get("mdoc", False)

        deploy_mode = "one-doc" if onedoc_enabled else "rc" if rc_enabled else "full"

        updated_sla, expected_outputs = check_correspondence(
            json_data, worker_list, cluster_names, deploy_mode
        )
        if updated_sla and root_group:
            global SYSTEM_MANAGER_URL
            SYSTEM_MANAGER_URL = root_group[0]

            # Save updated SLA JSON dict to file
            with open("/tmp/updated_sla.json", "w") as f:
                json.dump(updated_sla, f, indent=4)

            if not is_reachable(SYSTEM_MANAGER_URL):
                print(f"Error: Root node {SYSTEM_MANAGER_URL} is not reachable.")
                return

            token = authenticate(SYSTEM_MANAGER_URL)
            if token:
                global authToken
                authToken = token
                success, failed = await deploy_application(updated_sla)

                print(f"Success deploy {success}\n")
                print(f"Failed deply {failed}\n")

                if success:

                    # Wait for the applications to start
                    await asyncio.sleep(30)

                    running_processes, failed_processes = await application_healthcheck(
                        SYSTEM_MANAGER_URL, success, worker_list, expected_outputs
                    )

                    process_statuses = {
                        "running_processes": running_processes,
                        "failed_process": failed_processes,
                    }

                    # print("Service statuses:")
                    print(process_statuses)
                    # Save statuses JSON dict to file
                    # Filter out from statuses keys that are not IP addresses

                    with open("/tmp/process_statuses.json", "w") as f:
                        json.dump(process_statuses, f, indent=4)

                # if failed:
                # print("Failed to deploy applications:")
                # print(failed)
            else:
                print(
                    f"Failed to obtain authentication token from {SYSTEM_MANAGER_URL}."
                )
        else:
            print("Updated SLA is invalid or rootIP is empty.")
            print(updated_sla)
            print(root_group)

    else:
        print("Invalid topology data.")
        return None


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main_async())
    loop.close()


if __name__ == "__main__":
    main()
