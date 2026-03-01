# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final relationships."""

from uuid import uuid4

import pandas as pd

from graphrag.data_model.schemas import RELATIONSHIPS_FINAL_COLUMNS
from graphrag.index.operations.compute_degree import compute_degree
from graphrag.index.operations.compute_edge_combined_degree import (
    compute_edge_combined_degree,
)
from graphrag.index.operations.create_graph import create_graph


def finalize_relationships(
    relationships: pd.DataFrame,
) -> pd.DataFrame:
    """All the steps to transform final relationships."""
    # 检查关系是否为空
    if relationships.empty:
        # 如果为空，返回一个包含所有必要列的空DataFrame
        return pd.DataFrame(columns=RELATIONSHIPS_FINAL_COLUMNS)
        
    graph = create_graph(relationships)
    degrees = compute_degree(graph)

    final_relationships = relationships.drop_duplicates(subset=["source", "target"])
    
    # 检查关系是否包含必要的列
    if "source" not in final_relationships.columns or "target" not in final_relationships.columns:
        return pd.DataFrame(columns=RELATIONSHIPS_FINAL_COLUMNS)
        
    # 计算节点组合度
    try:
        final_relationships["combined_degree"] = compute_edge_combined_degree(
            final_relationships,
            degrees,
            node_name_column="title",
            node_degree_column="degree",
            edge_source_column="source",
            edge_target_column="target",
        )
    except Exception:
        # 如果计算组合度失败，创建默认值
        final_relationships["combined_degree"] = 0

    final_relationships.reset_index(inplace=True)
    final_relationships["human_readable_id"] = final_relationships.index
    final_relationships["id"] = final_relationships["human_readable_id"].apply(
        lambda _x: str(uuid4())
    )
    
    # 确保结果包含所有必要的列
    for column in RELATIONSHIPS_FINAL_COLUMNS:
        if column not in final_relationships.columns:
            if column == "description" and "description" not in final_relationships.columns:
                final_relationships[column] = ""
            else:
                final_relationships[column] = None

    return final_relationships.loc[
        :,
        RELATIONSHIPS_FINAL_COLUMNS,
    ]
