# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

from typing import Any

import pandas as pd

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.enums import AsyncType
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.operations.extract_graph.extract_graph import (
    extract_graph as extractor,
)
from graphrag.index.operations.summarize_descriptions import (
    summarize_descriptions,
)
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput
from graphrag.utils.storage import load_table_from_storage, write_table_to_storage


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """All the steps to create the base entity graph."""
    text_units = await load_table_from_storage("text_units", context.storage)

    extract_graph_llm_settings = config.get_language_model_config(
        config.extract_graph.model_id
    )
    extraction_strategy = config.extract_graph.resolved_strategy(
        config.root_dir, extract_graph_llm_settings
    )

    summarization_llm_settings = config.get_language_model_config(
        config.summarize_descriptions.model_id
    )
    summarization_strategy = config.summarize_descriptions.resolved_strategy(
        config.root_dir, summarization_llm_settings
    )

    entities, relationships, raw_entities, raw_relationships = await extract_graph(
        text_units=text_units,
        callbacks=context.callbacks,
        cache=context.cache,
        extraction_strategy=extraction_strategy,
        extraction_num_threads=extract_graph_llm_settings.concurrent_requests,
        extraction_async_mode=extract_graph_llm_settings.async_mode,
        entity_types=config.extract_graph.entity_types,
        summarization_strategy=summarization_strategy,
        summarization_num_threads=summarization_llm_settings.concurrent_requests,
    )

    await write_table_to_storage(entities, "entities", context.storage)
    await write_table_to_storage(relationships, "relationships", context.storage)

    if config.snapshots.raw_graph:
        await write_table_to_storage(raw_entities, "raw_entities", context.storage)
        await write_table_to_storage(
            raw_relationships, "raw_relationships", context.storage
        )

    return WorkflowFunctionOutput(
        result={
            "entities": entities,
            "relationships": relationships,
        }
    )


async def extract_graph(
    text_units: pd.DataFrame,
    callbacks: WorkflowCallbacks,
    cache: PipelineCache,
    extraction_strategy: dict[str, Any] | None = None,
    extraction_num_threads: int = 4,
    extraction_async_mode: AsyncType = AsyncType.AsyncIO,
    entity_types: list[str] | None = None,
    summarization_strategy: dict[str, Any] | None = None,
    summarization_num_threads: int = 4,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """All the steps to create the base entity graph."""
    # this returns a graph for each text unit, to be merged later
    extracted_entities, extracted_relationships = await extractor(
        text_units=text_units,
        callbacks=callbacks,
        cache=cache,
        text_column="text",
        id_column="id",
        strategy=extraction_strategy,
        async_mode=extraction_async_mode,
        entity_types=entity_types,
        num_threads=extraction_num_threads,
    )

    if not _validate_data(extracted_entities):
        callbacks.warning("警告：没有检测到实体。使用空实体数据框继续。")
        extracted_entities = pd.DataFrame(columns=["title", "type", "description", "text_unit_ids", "frequency"])
    
    if not _validate_data(extracted_relationships):
        callbacks.warning("警告：没有检测到关系。使用空关系数据框继续。")
        extracted_relationships = pd.DataFrame(columns=["source", "target", "description", "text_unit_ids", "weight"])

    # copy these as is before any summarization
    raw_entities = extracted_entities.copy()
    raw_relationships = extracted_relationships.copy()

    entities, relationships = await get_summarized_entities_relationships(
        extracted_entities=extracted_entities,
        extracted_relationships=extracted_relationships,
        callbacks=callbacks,
        cache=cache,
        summarization_strategy=summarization_strategy,
        summarization_num_threads=summarization_num_threads,
    )

    return (entities, relationships, raw_entities, raw_relationships)


async def get_summarized_entities_relationships(
    extracted_entities: pd.DataFrame,
    extracted_relationships: pd.DataFrame,
    callbacks: WorkflowCallbacks,
    cache: PipelineCache,
    summarization_strategy: dict[str, Any] | None = None,
    summarization_num_threads: int = 4,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Summarize the entities and relationships."""
    # 如果实体和关系都为空，直接返回空数据框
    if extracted_entities.empty and extracted_relationships.empty:
        return (
            pd.DataFrame(columns=["title", "type", "description"]), 
            pd.DataFrame(columns=["source", "target", "description", "weight"])
        )
    
    # 获取实体和关系的摘要
    entity_summaries, relationship_summaries = await summarize_descriptions(
        entities_df=extracted_entities,
        relationships_df=extracted_relationships,
        callbacks=callbacks,
        cache=cache,
        strategy=summarization_strategy,
        num_threads=summarization_num_threads,
    )
    
    # 处理关系
    if extracted_relationships.empty:
        relationships = pd.DataFrame(columns=["source", "target", "description", "weight"])
    else:
        # 确保关系DataFrame包含description列
        if "description" not in extracted_relationships.columns:
            extracted_relationships["description"] = ""
        
        # 确保关系摘要不为空
        if relationship_summaries.empty:
            relationships = extracted_relationships
        else:
            try:
                relationships = extracted_relationships.drop(columns=["description"]).merge(
                    relationship_summaries, on=["source", "target"], how="left"
                )
            except Exception as e:
                callbacks.warning(f"关系合并失败: {str(e)}，使用原始关系")
                relationships = extracted_relationships
    
    # 处理实体
    if extracted_entities.empty:
        entities = pd.DataFrame(columns=["title", "type", "description"])
    else:
        # 确保实体DataFrame包含description列
        if "description" not in extracted_entities.columns:
            extracted_entities["description"] = ""
        
        # 确保实体摘要不为空
        if entity_summaries.empty:
            entities = extracted_entities
        else:
            try:
                if "description" in extracted_entities.columns:
                    extracted_entities = extracted_entities.drop(columns=["description"])
                entities = extracted_entities.merge(entity_summaries, on="title", how="left")
            except Exception as e:
                callbacks.warning(f"实体合并失败: {str(e)}，使用原始实体")
                entities = extracted_entities
    
    return entities, relationships


def _validate_data(df: pd.DataFrame) -> bool:
    """Validate that the dataframe has data."""
    return not df.empty and len(df) > 0
