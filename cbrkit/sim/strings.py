import csv
import itertools
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from cbrkit.sim._taxonomy import Taxonomy, TaxonomyMeasure
from cbrkit.sim.generic import table as generic_table
from cbrkit.typing import (
    FilePath,
    SimPairFunc,
    SimSeq,
    SimSeqFunc,
    SimVal,
)


def _cosine(u, v) -> float:
    import numpy as np
    import scipy.spatial.distance as scipy_dist

    if np.any(u) and np.any(v):
        return cast(float, 1 - scipy_dist._cosine(u, v))

    return 0.0


def _unique_items(pairs: Sequence[tuple[str, str]]) -> list[str]:
    return [*{*itertools.chain.from_iterable(pairs)}]


def spacy(model_name: str = "en_core_web_lg") -> SimSeqFunc[str]:
    from spacy import load as spacy_load

    nlp = spacy_load(model_name)

    def wrapped_func(pairs: Sequence[tuple[str, str]]) -> SimSeq:
        texts = _unique_items(pairs)

        with nlp.select_pipes(enable=[]):
            _docs = nlp.pipe(texts)

        docs = dict(zip(texts, _docs, strict=True))

        return [docs[x].similarity(docs[y]) for x, y in pairs]

    return wrapped_func


def sentence_transformers(model_name: str) -> SimSeqFunc[str]:
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name)

    def wrapped_func(pairs: Sequence[tuple[str, str]]) -> SimSeq:
        texts = _unique_items(pairs)
        _vecs = model.encode(texts, convert_to_numpy=True)
        vecs = dict(zip(texts, _vecs, strict=True))

        return [_cosine(vecs[x], vecs[y]) for x, y in pairs]

    return wrapped_func


def openai(model_name: str) -> SimSeqFunc[str]:
    import numpy as np
    from openai import Client

    client = Client()

    def wrapped_func(pairs: Sequence[tuple[str, str]]) -> SimSeq:
        texts = _unique_items(pairs)
        res = client.embeddings.create(input=texts, model=model_name)
        _vecs = [np.array(x.embedding) for x in res.data]
        vecs = dict(zip(texts, _vecs, strict=True))

        return [_cosine(vecs[x], vecs[y]) for x, y in pairs]

    return wrapped_func


def taxonomy(
    path: FilePath, measure: TaxonomyMeasure = "wu_palmer"
) -> SimPairFunc[str]:
    taxonomy = Taxonomy(path)

    def wrapped_func(x: str, y: str) -> SimVal:
        return taxonomy.similarity(x, y, measure)

    return wrapped_func


def levenshtein(score_cutoff: float | None = None) -> SimPairFunc[str]:
    import Levenshtein

    def wrapped_func(x: str, y: str) -> SimVal:
        return Levenshtein.ratio(x, y, score_cutoff=score_cutoff)

    return wrapped_func


def jaro(score_cutoff: float | None = None) -> SimPairFunc[str]:
    import Levenshtein

    def wrapped_func(x: str, y: str) -> SimVal:
        return Levenshtein.jaro(x, y, score_cutoff=score_cutoff)

    return wrapped_func


def jaro_winkler(
    score_cutoff: float | None = None, prefix_weight: float | None = None
) -> SimPairFunc[str]:
    import Levenshtein

    def wrapped_func(x: str, y: str) -> SimVal:
        return Levenshtein.jaro_winkler(
            x, y, score_cutoff=score_cutoff, prefix_weight=prefix_weight
        )

    return wrapped_func


def table(
    entries: Sequence[tuple[str, str, SimVal]] | FilePath,
    symmetric: bool = True,
    default: SimVal = 0.0,
) -> SimPairFunc[str]:
    if isinstance(entries, FilePath):
        if isinstance(entries, str):
            entries = Path(entries)

        if entries.suffix != ".csv":
            raise NotImplementedError()

        with entries.open() as f:
            reader = csv.reader(f)
            parsed_entries = [(x, y, float(z)) for x, y, z in reader]

    else:
        parsed_entries = entries

    return generic_table(parsed_entries, symmetric=symmetric, default=default)
