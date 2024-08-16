import nltk
from fastapi import HTTPException

from typing import Callable

from metrics.metric_base import MetricBase


class Bleu(MetricBase):
    """
    Bleu metric class.

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

    def info(self) -> dict:
        return {
            "name": "bleu",
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
            return nltk.translate.bleu_score.sentence_bleu(
                references=references,
                hypothesis=hypothesis,
                weights=self.weights,
                smoothing_function=self.smoothing_function,
                auto_reweigh=self.auto_reweigh,
            )
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Could not calculate score because of error: {e}",
            )
