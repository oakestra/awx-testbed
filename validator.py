import json
import sys


def validate_topology(json_data):
    try:
        topology_descriptor = json_data["topology_descriptor"]

        # Validate one_doc_enabled
        if not isinstance(topology_descriptor.get("one_doc_enabled"), bool):
            return False

        # Validate together_root_cluster
        if not isinstance(topology_descriptor.get("together_root_cluster"), bool):
            return False

        # Validate cluster_list
        cluster_list = topology_descriptor.get("cluster_list")
        if not isinstance(cluster_list, list):
            return False

        for cluster in cluster_list:
            # Validate cluster_number
            if not isinstance(cluster.get("cluster_number"), int):
                return False
            # Validate number_of_nodes
            if not isinstance(cluster.get("number_of_nodes"), int):
                return False

            # Validate sla_descriptor inside cluster
            sla_descriptor = cluster.get("sla_descriptor")
            if sla_descriptor:
                # Validate sla_version
                if not isinstance(sla_descriptor.get("sla_version"), str):
                    return False
                # Validate customerID
                if not isinstance(sla_descriptor.get("customerID"), str):
                    return False
                # Validate applications list
                applications = sla_descriptor.get("applications")
                if not isinstance(applications, list):
                    return False

                for app in applications:
                    # Validate application_name
                    if not isinstance(app.get("application_name"), str):
                        return False
                    # Validate application_namespace
                    if not isinstance(app.get("application_namespace"), str):
                        return False
                    # Validate application_desc
                    if not isinstance(app.get("application_desc"), str):
                        return False
                    # Validate microservices list
                    microservices = app.get("microservices")
                    if not isinstance(microservices, list):
                        return False

                    for microservice in microservices:
                        # Validate microservice_name
                        if not isinstance(microservice.get("microservice_name"), str):
                            return False
                        # Validate microservice_namespace
                        if not isinstance(
                            microservice.get("microservice_namespace"), str
                        ):
                            return False
                        # Validate virtualization
                        if not isinstance(microservice.get("virtualization"), str):
                            return False
                        # Validate cmd
                        if not isinstance(microservice.get("cmd"), list):
                            return False
                        # Validate memory
                        if not isinstance(microservice.get("memory"), int):
                            return False
                        # Validate vcpus
                        if not isinstance(microservice.get("vcpus"), int):
                            return False
                        # Validate storage
                        if not isinstance(microservice.get("storage"), int):
                            return False
                        # Validate code
                        if not isinstance(microservice.get("code"), str):
                            return False
                        # Validate port
                        if not isinstance(microservice.get("port"), str):
                            return False

        return True

    except KeyError:
        return False
    except TypeError:
        return False


if __name__ == "__main__":
    json_file = sys.argv[1]

    with open(json_file, "r") as f:
        json_data = json.load(f)

    validity = validate_topology(json_data)

    if validity:
        print("true")
    else:
        print("false")
