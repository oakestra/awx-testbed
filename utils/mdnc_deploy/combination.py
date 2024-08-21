import sys
import ast
import json


def convert_python_literal_to_json(data):
    """Convert Python literal dictionary to JSON string."""
    return json.dumps(data, indent=4)


def compute_worker_cluster_association(data):
    """Compute the association between workers and clusters."""
    clusters = (
        data.get("topology_descriptor", {})
        .get("topology_descriptor", {})
        .get("cluster_list", [])
    )
    workers = data.get("group_workers_full", [])

    cluster_worker_map = {}
    worker_index = 0

    for cluster in clusters:
        cluster_number = cluster.get("cluster_number")
        number_of_nodes = cluster.get("number_of_nodes", 0)

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


def main():
    # Read the entire JSON-like string from stdin
    input_data_str = sys.stdin.read().strip()

    # Process the JSON-like string
    result = process_json_string(input_data_str)

    # Print the result
    print(result)


if __name__ == "__main__":
    main()
