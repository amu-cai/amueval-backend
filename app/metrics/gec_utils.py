from typing import Any
from gec_metrics.metrics import ERRANT

SPLIT_TAG = "X_CORRECTION_SPLIT_X"


def score_gec(expected: list[Any], out: list[Any], beta: float):
    """
    Score Grammatical Error Correction (GEC) outputs with ERRANT from gec-metrics.

    Parameters
    ----------
    expected : list[Any]
        Lines in the format `source X_CORRECTION_SPLIT_X ref 1 X_CORRECTION_SPLIT_X ref 2 ...`.
        Each line needs at least one reference. Lines with fewer references than
        the longest line are padded by repeating their own references, which does
        not change the best reference choice.
    out : list[Any]
        Corrected sentences.
    beta : float
        Beta for the F-beta score, also used to pick the best reference.

    Returns
    -------
    gec-metrics Score with precision, recall and f.
    """
    lines = [x.split(SPLIT_TAG) for x in expected]
    for i, line in enumerate(lines, start=1):
        if len(line) < 2:
            raise ValueError(f"line {i} of expected results has no reference")

    metric = ERRANT(ERRANT.Config(beta=beta))

    # gec-metrics splits sentences on whitespace only, so tokenise with spaCy
    # first, as the previous implementation did with `tokenise=True`.
    def tokenise(text: str) -> str:
        return " ".join(t.text for t in metric.errant.nlp.tokenizer(text))

    sources = [tokenise(line[0]) for line in lines]
    hypotheses = [tokenise(x) for x in out]
    refs_per_line = [[tokenise(ref) for ref in line[1:]] for line in lines]

    num_refs = max(len(refs) for refs in refs_per_line)
    references = [
        [refs[ref_id % len(refs)] for refs in refs_per_line]
        for ref_id in range(num_refs)
    ]

    return metric.score_corpus_verbose(sources, hypotheses, references)
