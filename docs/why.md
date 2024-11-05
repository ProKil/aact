## Why should I use AAct?

1. Non-blocking: the nodes are relatively independent of each other, so if you are waiting for users' input,
    you can still process sensor data in the background.
2. Scalable: you can a large number of nodes on one machine or distribute them across multiple machines.
3. Hackable: you can easily design your own nodes and connect them to the existing nodes.
4. Zero-code configuration: the `dataflow.toml` allows you to design the dataflow graph without writing any
    Python code.
