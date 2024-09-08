# AAct -- An actor model library in Python
*Designed for communicating sensors, neural networks, agents, users, and environments.*

## Installation

### Pre-requisites
- Python 3.10 or later
- pip
- Docker (for installing Redis)

### Install
```bash
pip install aact
```

### Examples
#### Tick and print
```bash
docker run -d --name redis-stack -p 6379:6379 -p 8001:8001 redis/redis-stack:latest
aact run-dataflow examples/example.toml
```

You will see a tick printed every second.

#### Looped speaker and listener
```bash
pip install aact[audio]
docker run -d --name redis-stack -p 6379:6379 -p 8001:8001 redis/redis-stack:latest
aact run-dataflow examples/speaker_listener.toml
```
