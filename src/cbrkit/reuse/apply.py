from collections.abc import Mapping, Sequence

from ..helpers import (
    get_metadata,
)
from ..model import QueryResultStep, Result, ResultStep
from ..typing import (
    Casebase,
    Float,
    ReuserFunc,
)


def apply_result[Q, C, V, S: Float](
    result: Result[Q, C, V, S] | ResultStep[Q, C, V, S],
    reusers: ReuserFunc[C, V, S] | Sequence[ReuserFunc[C, V, S]],
) -> Result[Q, C, V, S]:
    """Applies a single query to a casebase using reuser functions.

    Args:
        result: The result that will be used for the query.
        reusers: The reuser functions that will be applied to the casebase.

    Returns:
        Returns an object of type Result.
    """
    return apply_batches(
        {
            query_key: (entry.casebase, entry.query)
            for query_key, entry in result.queries.items()
        },
        reusers,
    )


def apply_batches[Q, C, V, S: Float](
    batch: Mapping[Q, tuple[Mapping[C, V], V]],
    reusers: ReuserFunc[C, V, S] | Sequence[ReuserFunc[C, V, S]],
) -> Result[Q, C, V, S]:
    if not isinstance(reusers, Sequence):
        reusers = [reusers]

    steps: list[ResultStep[Q, C, V, S]] = []
    current_batches: Mapping[Q, tuple[Mapping[C, V], V]] = batch

    for reuser in reusers:
        queries_results = reuser(list(current_batches.values()))
        step_queries = {
            query_key: QueryResultStep.build(
                adapted_sims,
                adapted_casebase,
                current_batches[query_key][1],
            )
            for query_key, (adapted_casebase, adapted_sims) in zip(
                current_batches.keys(), queries_results, strict=True
            )
        }

        steps.append(ResultStep(step_queries, get_metadata(reuser)))
        current_batches = {
            query_key: (step_queries[query_key].casebase, step_queries[query_key].query)
            for query_key in current_batches.keys()
        }

    return Result(steps)


def apply_queries[Q, C, V, S: Float](
    casebase: Mapping[C, V],
    queries: Mapping[Q, V],
    reusers: ReuserFunc[C, V, S] | Sequence[ReuserFunc[C, V, S]],
) -> Result[Q, C, V, S]:
    """Applies a single query to a casebase using reuser functions.

    Args:
        casebase: The casebase for the query.
        queries: The queries that will be used to adapt the casebase.
        reusers: The reuser functions that will be applied to the casebase.

    Returns:
        Returns an object of type Result
    """
    return apply_batches(
        {query_key: (casebase, query) for query_key, query in queries.items()},
        reusers,
    )


def apply_pair[V, S: Float](
    case: V,
    query: V,
    reusers: ReuserFunc[str, V, S] | Sequence[ReuserFunc[str, V, S]],
) -> Result[str, str, V, S]:
    """Applies a single query to a single case using reuser functions.

    Args:
        case: The case that will be used for the query.
        query: The query that will be applied to the case.
        reusers: The reuser functions that will be applied to the case.

    Returns:
        Returns an object of type Result.
    """
    return apply_queries(
        {"default": case},
        {"default": query},
        reusers,
    )


def apply_query[K, V, S: Float](
    casebase: Casebase[K, V],
    query: V,
    reusers: ReuserFunc[K, V, S] | Sequence[ReuserFunc[K, V, S]],
) -> Result[str, K, V, S]:
    """Applies a single query to a casebase using reuser functions.

    Args:
        casebase: The casebase that will be used for the query.
        query: The query that will be applied to the case.
        reusers: The reuser functions that will be applied to the case.

    Returns:
        Returns an object of type Result.
    """
    return apply_queries(casebase, {"default": query}, reusers)