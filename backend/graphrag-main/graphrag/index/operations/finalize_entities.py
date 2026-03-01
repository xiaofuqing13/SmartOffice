# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final entities."""

from uuid import uuid4

import pandas as pd

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.models.embed_graph_config import EmbedGraphConfig
from graphrag.data_model.schemas import ENTITIES_FINAL_COLUMNS
from graphrag.index.operations.compute_degree import compute_degree
from graphrag.index.operations.create_graph import create_graph
from graphrag.index.operations.embed_graph.embed_graph import embed_graph
from graphrag.index.operations.layout_graph.layout_graph import layout_graph


def finalize_entities(
    entities: pd.DataFrame,
    relationships: pd.DataFrame,
    callbacks: WorkflowCallbacks,
    embed_config: EmbedGraphConfig | None = None,
    layout_enabled: bool = False,
) -> pd.DataFrame:
    """All the steps to transform final entities."""
    # 检查实体或关系是否为空
    if entities.empty or relationships.empty:
        # 如果为空，返回一个包含所有必要列的空DataFrame
        empty_df = pd.DataFrame(columns=ENTITIES_FINAL_COLUMNS)
        return empty_df
        
    graph = create_graph(relationships)
    graph_embeddings = None
    if embed_config is not None and embed_config.enabled:
        graph_embeddings = embed_graph(
            graph,
            embed_config,
        )
    layout = layout_graph(
        graph,
        callbacks,
        layout_enabled,
        embeddings=graph_embeddings,
    )
    # 确保layout不为空
    if layout.empty:
        # 如果layout为空，使用默认值创建一个包含必要列的DataFrame
        layout = pd.DataFrame({
            "label": entities["title"],
            "x": 0,
            "y": 0,
            "size": 0
        })
        
    degrees = compute_degree(graph)
    # 确保degrees不为空
    if degrees.empty and not entities.empty:
        # 如果degrees为空但实体不为空，创建一个包含默认度数的DataFrame
        degrees = pd.DataFrame({
            "title": entities["title"],
            "degree": 0
        })
        
    final_entities = (
        entities.merge(layout, left_on="title", right_on="label", how="left")
        .merge(degrees, on="title", how="left")
        .drop_duplicates(subset="title")
    )
    final_entities = final_entities[final_entities["title"].notna()].reset_index(drop=True)
    # disconnected nodes and those with no community even at level 0 can be missing degree
    final_entities["degree"] = final_entities["degree"].fillna(0).astype(int)
    final_entities.reset_index(inplace=True)
    final_entities["human_readable_id"] = final_entities.index
    final_entities["id"] = final_entities["human_readable_id"].apply(
        lambda _x: str(uuid4())
    )
    
    # 确保结果包含所有必要的列
    for column in ENTITIES_FINAL_COLUMNS:
        if column not in final_entities.columns:
            final_entities[column] = None
            
    return final_entities.loc[
        :,
        ENTITIES_FINAL_COLUMNS,
    ]
