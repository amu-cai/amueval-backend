from sklearn import metrics as sk_metrics
from typing import Any
from fastapi import HTTPException
from metrics.metric_base import MetricBase


class NDCG(MetricBase):
    """
    Normalized discounted cumulative gain metric class.

    Parameters
    ----------
    k : int | None, default None
        Only consider the highest k scores in the ranking. If None, use all
        outputs.
    sample_weight : list[Any] | None, default None
        Sample weights.
    ignore_ties : bool, default False
        Assume that there are no ties in expected.
    """

    k: int | None = None
    sample_weight: list[Any] | None = None
    ignore_ties: bool = False

    def info(self) -> dict:
        return {
            "name": "Normalized discounted cumulative gain",
            "link": "https://scikit-learn.org/stable/modules/generated/sklearn.metrics.dcg_score.html#sklearn.metrics.dcg_score",
            "parameters": [
                {"name": "k", "data_type": "int | None", "default_value": "None"},
                {
                    "name": "sample_weight",
                    "data_type": "list[Any] | None",
                    "default_value": "None",
                },
                {"name": "ignore_ties", "data_type": "bool", "default_value": "False"},
            ],
        }

    def calculate(
        self,
        expected: list[Any],
        out: list[Any],
    ) -> float | int:
        """
        Metric calculation.

        Parameters
        ----------
        expected : list[Any]
            List with expected values.
        out : list[Any]
            List with actual values.

        Returns
        -------
        Value of the metric.
        """
        try:
            return sk_metrics.ndcg_score(
                y_true=expected,
                y_pred=out,
                k=self.k,
                sample_weight=self.sample_weight,
                ignore_ties=self.ignore_ties,
            )
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Could not calculate score because of error: {e}",
            )
