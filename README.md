# [⚙️ Oakestra Virtual Testbed](https://github.com/oakestra/awx-testbed)

The primary objective of this repository is to offer Oakestra maintainers and contributors a CI-integrated tool for automating component deployment, configuration, application deployment, and result assessment across a range of predefined and customizable use cases and scenarios.
To achieve this, two execution modes have been identified:

- **Custom Execution**: Available to maintainers of the Oakestra repository with write access, enabling them to test specific scenarios against particular versions of Oakestra and Oakestra-Net.
- **Oneshot Execution**: Integrated into the CI pipeline, it runs a predefined set of scenarios for each approved PR review, providing a pass/fail status based on the success of the deployment and tests.

Although the two execution modes share common elements, their differing behavior necessitates separating the testbed into two branches: `custom` for Custom Execution and `oneshot` for Oneshot Execution.

## Topology Descriptor
By *use cases* or *scenarios*, we mean a specific configuration of multiple nodes, which can function as root, cluster, or worker nodes, and have applications deployed on them with defined constraints regarding where these deployments should occur. 

To facilitate this, we introduced the concept of a **Topology Descriptor** *(TD)*, a JSON file that specify which deployment mode execute among *1-DOC (One device, One Cluster), M-DOC ($M$ Devices, One Cluster)* and *MDNC ($M$ Devices, $N$ Clusters)*. For more information about deployment mode, please refer [Create your first cluster](https://www.oakestra.io/docs/getstarted/get-started-cluster/#create-your-first-oakestra-cluster). 

So a *TD* add meta-information to one or more [Deployment Descriptor](https://www.oakestra.io/docs/getstarted/get-started-app/#deployment-descriptor)(s), slightly modifying it temporarly for testing purpose, as we will explain later.

### Anatonomy of a Topology Descriptor
The general struscture of a *TD* is the following, mostly shared with the structure of a Deployment Descriptor:
```json
{
  "topology_descriptor": {
    "onedoc": "boolean", 
    "mdoc": "boolean",
    "cluster_list": [
      {
        "cluster_number": "integer", 
        "workers_number": "integer",
        "sla_descriptor": {
          "sla_version": "string", 
          "customerID": "string",
          "applications": [
            {
              "applicationID": "string", 
              "application_name": "string", 
              "application_namespace": "string",
              "application_desc": "string",
              "microservices": [
                {
                  "microserviceID": "string", 
                  "microservice_name": "string", 
                  "microservice_namespace": "string",
                  "virtualization": "string", 
                  "cmd": ["array of strings"], 
                  "expected_output": "string", 
                  "memory": "integer", 
                  "vcpus": "integer", 
                  "vgpus": "integer", 
                  "vtpus": "integer", 
                  "bandwidth_in": "integer", 
                  "bandwidth_out": "integer", 
                  "storage": "integer", 
                  "code": "string", 
                  "state": "string", 
                  "port": "string", 
                  "added_files": ["array of strings"],
                  "constraints": ["array of strings"]
                }
              ]
            }
          ]
        }
      }
    ]
  }
}

```
Let's describe the meaning of the fields introduced by the *TD*:

- **`onedoc`**: If `true`, provisions the infrastructure to deploy and test the component on a single node.
- **`mdoc`**: If `true`, provisions the infrastructure to deploy the Root and Cluster Orchestrator on a single node, and provisions $M$ additional nodes.
  - If both `onedoc` and `mdoc` are `false`, the assumed scenario is `mdnc`.
- **`cluster_list`**: Contains the list of clusters to be deployed, based on the previous two flags. It includes three key pieces of information:
  - **`cluster_number`**: An integer identifying the specific cluster.
  - **`workers_number`**: An integer specifying the number of worker nodes to deploy in the cluster (assigned if enough hosts are available).
    - ℹ️ Within the same cluster, if `workers_number` is greater than 1, applications are deployed on specific worker nodes using a round-robin assignment, where each application is assigned to a worker node in turn.  
If there is only one application, its microservices are distributed across the worker nodes using the same round-robin assignment policy.

 - **`sla_descriptor`**: Contains the same information as the [Deployment Descriptor](https://www.oakestra.io/docs/getstarted/get-started-app/#deployment-descriptor), with an additional field, `expected_output`, used only by the testbed. This field is not required or used by Oakestra and is removed before deploying the related applications. It allows the testbed to compare the logs of specific microservices against the defined `expected_output`, serving as a basic health check for the microservice.

## Usage

### 1. Custom Execution
Mantainers that have write access to oakestra repository can find under *Actions* tab in Github the corresponding action called "**Execute Custom Testbed Workflow Pipeline**". Click on *Run Workflow* will make appear the following box:
![](./imgs/custom_trigger_1.png)



### Expected Behaviours




## Technical Documentation
