import evaluate
import json
from fastapi import HTTPException

from typing import Callable

from metrics.metric_base import MetricBase


class ChrfPP(MetricBase):
    """
    Chrf++ metric class.

    Parameters
    ----------
    weights : tuple[float] | list[tuple[float]], default (0.25, 0.25, 0.25, 0.25)
        Weights for unigrams, bigrams, trigrams and so on.
    smoothing_function : Callable | None, default None
    auto_reweigh : bool, default False
        Option to re-normalize the weights uniformly.
    sorting: str, default "ascending"
        Information about the value of the metric.
    """

    weights: tuple[float] = (0.25, 0.25, 0.25, 0.25)
    smoothing_function: Callable | None = None
    auto_reweigh: bool = False
    sorting: str = "ascending"
    chrf_tool: Callable = evaluate.load("chrf")

    def info(self) -> dict:
        return {
            "name": "chrf_pp",
            "link": "https://www.nltk.org/api/nltk.translate.bleu_score.html",
            "parameters": [
                {
                    "name": "weights",
                    "data_type": "tuple[float] | list[tuple[float]]",
                    "default_value": "(0.25, 0.25, 0.25, 0.25)",
                },
                {
                    "name": "smoothing_function",
                    "data_type": "Callable",
                    "default_value": "None",
                },
                {
                    "name": "auto_reweigh",
                    "data_type": "bool",
                    "default_value": "False",
                },
            ],
        }

    def calculate(
        self,
        references: list[list[str]],
        hypothesis: list[str],
    ) -> float | list[float]:
        """
        Metric calculation.

        Parameters
        ----------
        references : list[list[str]]
            List with reference sentences.
        hypothesis : list[str]
            List with hypothesis sentence.

        Returns
        -------
        Value of the metric.
        """
        try:
            refs = []
            for r in references:
                refs.append(json.loads(r.strip()))
            
            hyps = []
            for h in hypothesis:
                hyps.append(json.loads(h.strip()))

            generations = [x["generated_target"] for x in hyps]
            gold_labels = [x["target"] for x in refs]

            results = self.chrf_tool.compute(predictions=generations, references=gold_labels, word_order=2)
            return results['score']
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Could not calculate score because of error: {e}",
            )
