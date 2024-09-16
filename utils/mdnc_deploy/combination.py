import sys
import ast
import json


def convert_python_literal_to_json(data):
    """Convert Python literal dictionary to JSON string."""
    return json.dumps(data, indent=4)


def compute_worker_cluster_association(json_data, cluster_list=None, workers=None):
    """Compute the association between workers and clusters."""

    clusters = json_data.get("topology_descriptor", {}).get("cluster_list", [])

    # print(f"clusters: {clusters}")

    cluster_worker_map = {}
    worker_index = 0

    for cluster in clusters:
        cluster_number = cluster.get("cluster_number")
        number_of_nodes = cluster.get("workers_number", 0)

        if number_of_nodes > 0:
            cluster_worker_map[cluster_number] = []
            for _ in range(number_of_nodes):
                if worker_index < len(workers):
                    cluster_worker_map[cluster_number].append(workers[worker_index])
                    worker_index += 1

    return cluster_worker_map


def process_json_string(json_str):
    """Process JSON string to compute worker-cluster association."""
    try:
        # Convert JSON-like string with single quotes to a Python dictionary
        data = ast.literal_eval(json_str)
    except (SyntaxError, ValueError) as e:
        return f"Error parsing input: {e}"

    # Compute the association between workers and clusters
    association = compute_worker_cluster_association(data)

    # Convert the result to a JSON string and return it
    return convert_python_literal_to_json(association)


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


def main():
    # Read the entire JSON-like string from stdin

    topology_descriptor_filepath, cluster_str, worker_str = sys.argv[1:4]
    try:
        with open(topology_descriptor_filepath, "r") as f:
            json_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading JSON file: {e}")
        return

    # print(f"json_data: {json_data.get('topology_descriptor')}")

    worker_list = check_list(worker_str)
    cluster_list = check_list(cluster_str)

    association = compute_worker_cluster_association(
        json_data, cluster_list, worker_list
    )

    # Process the JSON-like string

    # Print the result
    print(association)


if __name__ == "__main__":
    main()
