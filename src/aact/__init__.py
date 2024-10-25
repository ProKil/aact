r"""
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

## Why should I use AAct?

1. Non-blocking: the nodes are relatively independent of each other, so if you are waiting for users' input,
    you can still process sensor data in the background.
2. Scalable: you can a large number of nodes on one machine or distribute them across multiple machines.
3. Hackable: you can easily design your own nodes and connect them to the existing nodes.
4. Zero-code configuration: the `dataflow.toml` allows you to design the dataflow graph without writing any
    Python code.

# Quickstart

## Installation

System requirement:

1. Python 3.10 or higher
2. Redis server

<details>

<summary>Redis installation</summary>

The easiest way to install Redis is to use Docker:
```bash
docker run -d --name redis-stack -p 6379:6379 -p 8001:8001 redis/redis-stack:latest
```
According to your system, you can also install Redis from the official website: https://redis.io/download

Note: we will only require a standard Redis server (without RedisJSON / RedisSearch) in this library.

</details>

```bash
pip install aact
```

<details>
<summary> from source </summary>

```bash
git clone https://github.com/ProKil/aact.git
cd aact
pip install .
```

For power users, please use `uv` for package management.
</details>


## Quick Start Example

Assuming your Redis is hosted on `localhost:6379` using docker.
You can create a `dataflow.toml` file:

```toml
redis_url = "redis://localhost:6379/0" # required

[[nodes]]
node_name = "print"
node_class = "print"

[nodes.node_args.print_channel_types]
"tick/secs/1" = "tick"

[[nodes]]
node_name = "tick"
node_class = "tick"
```

To run the dataflow:
```bash
aact run-dataflow dataflow.toml
```

This will start the `tick` node and the `print` node. The `tick` node sends a message every second to the `print` node, which prints the message to the console.

## Usage

### CLI

You can start from CLI and progress to more advanced usages.

1. `aact --help` to see all commands
2. `aact run-dataflow <dataflow_name.toml>`  to run a dataflow. Check [Dataflow.toml syntax](#dataflowtoml-syntax)
3. `aact run-node` to run one node in a dataflow.
4. `aact draw-dataflow <dataflow_name_1.toml> <dataflow_name_2.toml> --svg-path <output.svg>` to draw dataflow.


### Customized Node

Here is the minimal knowledge you would need to implement a customized node.

```python
from aact import Node, NodeFactory, Message

@NodeFactory.register("node_name")
class YourNode(Node[your_input_type, your_output_type]):

    # event_handler is the only function your **have** to implement
    def event_handler(self, input_channel: str, input_message: Message[your_input_type]) -> AsyncIterator[str, Message[your_output_type]]:
        match input_channel:
            case input_channel_1:
                <do_your_stuff>
                yield output_channel_1, Message[your_output_type](data=your_output_message)
            case input_channel_2:
                ...

   # implement other functions: __init__, _wait_for_input, event_loop, __aenter__, __aexit__

# To run a node without CLI
async with NodeFactory.make("node_name", arg_1, arg_2) as node:
    await node.event_loop()
```

## Concepts

There are three important concepts to understand aact.

```mermaid
graph TD
    n1[Node 1] -->|channel_1| n2[Node 2]
```

### Nodes

Nodes (`aact.Nodes`) are designed to run in parallel asynchronously. This design is especially useful for deploying the nodes onto different machines.
A node should inherit `aact.Node` class, which extends `pydantic.BaseModel`.

### Channels

Channel is an inherited concept from Redis Pub/Sub. You can think of it as a radio channel.
Multiple publishers (nodes) can publish messages to the same channel, and multiple subscribers (nodes) can subscribe to the same channel.

### Messages

Messages are the data sent through the channels. Each message type is a class in the format of `Message[T]` , where `T` is a subclass or a union of subclasses of `DataModel`.

#### Customized Message Type

If you want to create a new message type, you can create a new class that inherits from `DataModel`.
```python
@DataModelFactory.register("new_type")
class NewType(DataModel):
    new_type_data: ... = ...


# For example
@DataModelFactory.register("integer")
class Integer(DataModel):
    integer_data: int = Field(default=0)
```

## Dataflow.toml syntax

```toml
redis_url = "redis://..." # required
extra_modules = ["package1.module1", "package2.module2"] # optional

[[nodes]]
node_name = "node_name_1" # A unique name in the dataflow
node_class = "node_class_1" # node_class should match the class name passed into NodeFactory.register

[node.node_args]
node_arg_1 = "value_1"

[[nodes]]
node_name = "node_name_2"
node_class = "node_class_2"

# ...
```


"""

from .nodes import Node, NodeFactory
from .messages import Message

__all__ = ["Node", "NodeFactory", "Message", "nodes", "messages", "cli"]
