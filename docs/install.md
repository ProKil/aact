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
