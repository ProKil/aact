import base64
from collections import defaultdict
import logging
import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomlkit as tomllib
from pydantic import BaseModel, ConfigDict, Field

import requests

from ...nodes.registry import NodeFactory


class NodeArgs(BaseModel):
    model_config = ConfigDict(extra="allow")


class NodeConfig(BaseModel):
    node_name: str
    node_class: str
    node_args: NodeArgs = Field(default_factory=NodeArgs)


class Config(BaseModel):
    redis_url: str = Field()
    extra_modules: list[str] = Field(default_factory=lambda: list())
    nodes: list[NodeConfig]


def get_dataflow_config(dataflow_toml: str) -> Config:
    """Get the dataflow configuration from a TOML file.

    Args:
        dataflow_toml (str): Path to the TOML file.

    Returns:
        Config: The dataflow configuration object.

    """
    logger = logging.getLogger(__name__)
    config = Config.model_validate(tomllib.load(open(dataflow_toml, "rb")))
    logger.info(f"Starting dataflow with config {config}")

    return config


def draw_dataflow_mermaid(
    configs: list[Config],
    config_names: list[str] | None = None,
    svg_path: str | None = None,
) -> None:
    """Draw the dataflow graph from the configuration.

    Args:
        config (Config): The dataflow configuration object.

    """

    edge2start_nodes_end_nodes: dict[str, tuple[list[str], list[str]]] = defaultdict(
        lambda: ([], [])
    )
    config_name2nodes: dict[str, list[str]] = defaultdict(list)
    node2config_name: dict[str, str] = {}

    if not config_names:
        config_names = [f"config_{i}" for i in range(len(configs))]
    else:
        assert len(config_names) == len(
            configs
        ), "The number of names should be equal to the number of configs."

    for config, config_name in zip(configs, config_names):
        for module in config.extra_modules:
            __import__(module)

        for node_config in config.nodes:
            node_class = node_config.node_class
            node_name = node_config.node_name
            node_args = node_config.node_args

            node = NodeFactory.make(
                node_class, **node_args.model_dump(), redis_url=config.redis_url
            )
            for input_channel in node.input_channel_types:
                edge2start_nodes_end_nodes[input_channel][1].append(node_name)

            for output_channel in node.output_channel_types:
                edge2start_nodes_end_nodes[output_channel][0].append(node_name)
            node2config_name[node_name] = config_name
            config_name2nodes[config_name].append(node_name)

    graph_str = "flowchart TD\n"
    invisible_nodes: list[str] = []

    for edge, (start_nodes, end_nodes) in edge2start_nodes_end_nodes.items():
        if len(start_nodes) > 1 or len(end_nodes) > 1:
            invisible_edge_node = f"invisible_edge_{edge}"
            invisible_nodes.append(invisible_edge_node)
            if not len(start_nodes):
                hidden_start_node = f"hidden_start_{edge}"
                graph_str += f"    {hidden_start_node}(( )) ---|{edge}| {invisible_edge_node}[ ]\n"
            else:
                for start_node in start_nodes:
                    graph_str += f"    {start_node}[{[start_node]}] ---|{edge}| {invisible_edge_node}[ ]\n"
            if not len(end_nodes):
                hidden_end_node = f"hidden_end_{edge}"
                graph_str += f"    {invisible_edge_node} --- {hidden_end_node}(( ))\n"
            else:
                for end_node in end_nodes:
                    graph_str += (
                        f"    {invisible_edge_node} ---> {end_node}[{[end_node]}]\n"
                    )
            config_name = ""
            if start_nodes:
                config_name = node2config_name[start_nodes[0]]
            elif end_nodes:
                config_name = node2config_name[end_nodes[0]]
            if all(
                [
                    node2config_name[start_node] == config_name
                    for start_node in start_nodes
                ]
            ) and all(
                [node2config_name[end_node] == config_name for end_node in end_nodes]
            ):
                config_name2nodes[config_name].append(invisible_edge_node)
        elif not len(start_nodes):
            hidden_start_node = f"hidden_start_{edge}"
            for end_node in end_nodes:
                graph_str += f"    {hidden_start_node}(( )) --->|{edge}| {end_node}[{[end_node]}]\n"
        elif not len(end_nodes):
            hidden_end_node = f"hidden_end_{edge}"
            for start_node in start_nodes:
                graph_str += f"    {start_node}[{[start_node]}] --->|{edge}| {hidden_end_node}(( ))\n"
        elif len(start_nodes) == 1 and len(end_nodes) == 1:
            graph_str += f"    {start_nodes[0]}[{[start_nodes[0]]}] --->|{edge}| {end_nodes[0]}[{[end_nodes[0]]}]\n"
        else:
            raise ValueError("This should not happen.")

    for config_name, node_names in config_name2nodes.items():
        graph_str += f"subgraph {config_name}\n"
        for node_name in node_names:
            graph_str += f"    {node_name}\n"
        graph_str += "end\n"

    for invisible_node in invisible_nodes:
        graph_str += f"    style {invisible_node} height:0px;\n"

    print(graph_str)

    if svg_path:
        graph_bytes = graph_str.encode("utf8")
        base64_bytes = base64.b64encode(graph_bytes)
        base64_string = base64_bytes.decode("ascii")

        url = f"https://mermaid.ink/svg/{base64_string}"
        response = requests.get(url)
        response.raise_for_status()

        with open(svg_path, "wb") as f:
            f.write(response.content)
