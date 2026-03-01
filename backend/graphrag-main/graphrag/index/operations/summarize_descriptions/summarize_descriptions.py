# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing the summarize_descriptions verb."""

import asyncio
import logging
from typing import Any

import pandas as pd

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.index.operations.summarize_descriptions.typing import (
    SummarizationStrategy,
    SummarizeStrategyType,
)
from graphrag.logger.progress import ProgressTicker, progress_ticker

log = logging.getLogger(__name__)


async def summarize_descriptions(
    entities_df: pd.DataFrame,
    relationships_df: pd.DataFrame,
    callbacks: WorkflowCallbacks,
    cache: PipelineCache,
    strategy: dict[str, Any] | None = None,
    num_threads: int = 4,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Summarize entity and relationship descriptions from an entity graph, using a language model."""
    log.debug("summarize_descriptions strategy=%s", strategy)
    
    # 检查输入数据框是否为空
    if entities_df.empty and relationships_df.empty:
        # 如果两者都为空，返回空的DataFrame
        log.info("输入的实体和关系数据框均为空，跳过摘要生成")
        return pd.DataFrame(columns=["title", "description"]), pd.DataFrame(columns=["source", "target", "description"])
    
    strategy = strategy or {}
    strategy_exec = load_strategy(
        strategy.get("type", SummarizeStrategyType.graph_intelligence)
    )
    strategy_config = {**strategy}

    # if max_retries is not set, inject a dynamically assigned value based on the maximum number of expected LLM calls to be made
    if strategy_config.get("llm") and strategy_config["llm"]["max_retries"] == -1:
        strategy_config["llm"]["max_retries"] = len(entities_df) + len(relationships_df)

    async def get_summarized(
        nodes: pd.DataFrame, edges: pd.DataFrame, semaphore: asyncio.Semaphore
    ):
        # 处理空的实体DataFrame
        if nodes.empty:
            entity_descriptions = pd.DataFrame(columns=["title", "description"])
        else:
            # 确保节点数据框有title和description列
            if "title" not in nodes.columns:
                log.warning("实体数据框中缺少'title'列，跳过实体摘要生成")
                entity_descriptions = pd.DataFrame(columns=["title", "description"])
            elif "description" not in nodes.columns:
                log.warning("实体数据框中缺少'description'列，跳过实体摘要生成")
                entity_descriptions = pd.DataFrame(columns=["title", "description"])
            else:
                ticker_length = len(nodes)
                ticker = progress_ticker(callbacks.progress, ticker_length)

                node_futures = [
                    do_summarize_descriptions(
                        str(row.title),  # type: ignore
                        sorted(set(row.description)) if isinstance(row.description, list) else [str(row.description)],  # type: ignore
                        ticker,
                        semaphore,
                    )
                    for row in nodes.itertuples(index=False)
                ]

                node_results = await asyncio.gather(*node_futures)

                node_descriptions = [
                    {
                        "title": result.id,
                        "description": result.description,
                    }
                    for result in node_results
                ]

                entity_descriptions = pd.DataFrame(node_descriptions)
                
        # 处理空的关系DataFrame
        if edges.empty:
            relationship_descriptions = pd.DataFrame(columns=["source", "target", "description"])
        else:
            # 确保边数据框有source、target和description列
            if "source" not in edges.columns or "target" not in edges.columns:
                log.warning("关系数据框中缺少'source'或'target'列，跳过关系摘要生成")
                relationship_descriptions = pd.DataFrame(columns=["source", "target", "description"])
            elif "description" not in edges.columns:
                log.warning("关系数据框中缺少'description'列，跳过关系摘要生成")
                relationship_descriptions = pd.DataFrame(columns=["source", "target", "description"])
            else:
                ticker_length = len(edges)
                ticker = progress_ticker(callbacks.progress, ticker_length)

                edge_futures = [
                    do_summarize_descriptions(
                        (str(row.source), str(row.target)),  # type: ignore
                        sorted(set(row.description)) if isinstance(row.description, list) else [str(row.description)],  # type: ignore
                        ticker,
                        semaphore,
                    )
                    for row in edges.itertuples(index=False)
                ]

                edge_results = await asyncio.gather(*edge_futures)

                edge_descriptions = [
                    {
                        "source": result.id[0],
                        "target": result.id[1],
                        "description": result.description,
                    }
                    for result in edge_results
                ]

                relationship_descriptions = pd.DataFrame(edge_descriptions)
                
        return entity_descriptions, relationship_descriptions

    async def do_summarize_descriptions(
        id: str | tuple[str, str],
        descriptions: list[str],
        ticker: ProgressTicker,
        semaphore: asyncio.Semaphore,
    ):
        async with semaphore:
            results = await strategy_exec(
                id, descriptions, callbacks, cache, strategy_config
            )
            ticker(1)
        return results

    semaphore = asyncio.Semaphore(num_threads)

    # 如果实体为空，创建一个仅有必要列的空DataFrame
    if entities_df.empty:
        entities_df = pd.DataFrame(columns=["title", "description"])
    
    # 如果关系为空，创建一个仅有必要列的空DataFrame
    if relationships_df.empty:
        relationships_df = pd.DataFrame(columns=["source", "target", "description"])
        
    try:
        return await get_summarized(entities_df, relationships_df, semaphore)
    except Exception as e:
        log.error(f"摘要生成过程中发生错误: {str(e)}")
        # 发生错误时返回空的数据框
        return pd.DataFrame(columns=["title", "description"]), pd.DataFrame(columns=["source", "target", "description"])


def load_strategy(strategy_type: SummarizeStrategyType) -> SummarizationStrategy:
    """Load strategy method definition."""
    match strategy_type:
        case SummarizeStrategyType.graph_intelligence:
            from graphrag.index.operations.summarize_descriptions.graph_intelligence_strategy import (
                run_graph_intelligence,
            )

            return run_graph_intelligence
        case _:
            msg = f"Unknown strategy: {strategy_type}"
            raise ValueError(msg)
