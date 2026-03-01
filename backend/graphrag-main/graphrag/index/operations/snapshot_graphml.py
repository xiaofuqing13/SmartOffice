# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing snapshot_graphml method definition."""

import networkx as nx

from graphrag.storage.pipeline_storage import PipelineStorage


async def snapshot_graphml(
    input: str | nx.Graph,
    name: str,
    storage: PipelineStorage,
) -> None:
    """Take a entire snapshot of a graph to standard graphml format."""
    # 如果输入为None或者是一个空图，保存一个空的GraphML文件
    if input is None:
        await storage.set(name + ".graphml", '<?xml version="1.0" encoding="UTF-8"?>\n<graphml></graphml>')
        return
        
    if isinstance(input, nx.Graph) and len(input.nodes) == 0:
        await storage.set(name + ".graphml", '<?xml version="1.0" encoding="UTF-8"?>\n<graphml></graphml>')
        return
        
    graphml = input if isinstance(input, str) else "\n".join(nx.generate_graphml(input))
    await storage.set(name + ".graphml", graphml)
