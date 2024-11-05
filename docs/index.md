# What is AAct?

AAct is designed for communicating sensors, neural networks, agents, users, and environments.


<details>
<summary>Can you expand on that?</summary>

AAct is a Python library for building asynchronous, actor-based, concurrent systems.
Specifically, it is designed to be used in the context of building systems with
components that communicate with each other but don't block each other.
</details>

## How does AAct work?

AAct is built around the concept of nodes and dataflow, where nodes are self-contained units
which receive messages from input channels, process the messages, and send messages to output channels.
Nodes are connected to each other to form a dataflow graph, where messages flow from one node to another.
Each node runs in its own event loop, and the nodes communicate with each other using Redis Pub/Sub.
