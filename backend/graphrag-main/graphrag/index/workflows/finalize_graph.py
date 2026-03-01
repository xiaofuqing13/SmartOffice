# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import pandas as pd
import networkx as nx

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.models.embed_graph_config import EmbedGraphConfig
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.data_model.schemas import ENTITIES_FINAL_COLUMNS, RELATIONSHIPS_FINAL_COLUMNS
from graphrag.index.operations.create_graph import create_graph
from graphrag.index.operations.finalize_entities import finalize_entities
from graphrag.index.operations.finalize_relationships import finalize_relationships
from graphrag.index.operations.snapshot_graphml import snapshot_graphml
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput
from graphrag.utils.storage import load_table_from_storage, write_table_to_storage


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """All the steps to create the base entity graph."""
    entities = await load_table_from_storage("entities", context.storage)
    relationships = await load_table_from_storage("relationships", context.storage)

    final_entities, final_relationships = finalize_graph(
        entities,
        relationships,
        callbacks=context.callbacks,
        embed_config=config.embed_graph,
        layout_enabled=config.umap.enabled,
    )

    await write_table_to_storage(final_entities, "entities", context.storage)
    await write_table_to_storage(final_relationships, "relationships", context.storage)

    if config.snapshots.graphml:
        try:
            # 检查关系是否为空
            if final_relationships.empty:
                # 如果关系为空，创建一个空图
                graph = nx.Graph()
            else:
                # 否则正常创建图
                graph = create_graph(final_relationships, edge_attr=["weight"])

            await snapshot_graphml(
                graph,
                name="graph",
                storage=context.storage,
            )
        except Exception as e:
            # 如果创建图或保存图时出错，记录警告并继续
            context.callbacks.warning(f"创建或保存图时出错: {str(e)}")

    return WorkflowFunctionOutput(
        result={
            "entities": entities,
            "relationships": relationships,
        }
    )


def finalize_graph(
    entities: pd.DataFrame,
    relationships: pd.DataFrame,
    callbacks: WorkflowCallbacks,
    embed_config: EmbedGraphConfig | None = None,
    layout_enabled: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """All the steps to finalize the entity and relationship formats."""
    # 检查输入是否为空
    if entities.empty and relationships.empty:
        # 如果都为空，返回两个空数据框
        return (
            pd.DataFrame(columns=ENTITIES_FINAL_COLUMNS),
            pd.DataFrame(columns=RELATIONSHIPS_FINAL_COLUMNS)
        )
    
    # 处理实体
    try:
        final_entities = finalize_entities(
            entities, relationships, callbacks, embed_config, layout_enabled
        )
    except Exception as e:
        # 如果处理实体时发生错误，记录警告并返回空数据框
        callbacks.warning(f"处理实体时发生错误: {str(e)}，使用空实体数据框代替")
        final_entities = pd.DataFrame(columns=ENTITIES_FINAL_COLUMNS)
        
    # 处理关系
    try:
        final_relationships = finalize_relationships(relationships)
    except Exception as e:
        # 如果处理关系时发生错误，记录警告并返回空数据框
        callbacks.warning(f"处理关系时发生错误: {str(e)}，使用空关系数据框代替")
        final_relationships = pd.DataFrame(columns=RELATIONSHIPS_FINAL_COLUMNS)
        
    return (final_entities, final_relationships)
