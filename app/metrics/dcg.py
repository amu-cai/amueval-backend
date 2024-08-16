from sklearn import metrics as sk_metrics
from typing import Any
from fastapi import HTTPException
from metrics.metric_base import MetricBase


class DCG(MetricBase):
    """
    Discounted cumulative gain metric class.

    Parameters
    ----------
    k : int | None, default None
        Only consider the highest k scores in the ranking. If None, use all
        outputs.
    log_base : float, default 2.0
        Base of the logarithm used for the discount.
    sample_weight : list[Any] | None, default None
        Sample weights.
    ignore_ties : bool, default False
        Assume that there are no ties in expected.
    sorting: str, default "ascending"
        Information about the value of the metric.
    """

    k: int | None = None
    log_base: float = 2.0
    sample_weight: list[Any] | None = None
    ignore_ties: bool = False
    sorting: str = "ascending"

    def info(self) -> dict:
        return {
            "name": "Discounted cumulative gain",
            "link": "https://scikit-learn.org/stable/modules/generated/sklearn.metrics.dcg_score.html#sklearn.metrics.dcg_score",
            "parameters": [
                {"name": "k", "data_type": "int | None", "default_value": "None"},
                {"name": "log_base", "data_type": "float", "default_value": "2.0"},
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
            return sk_metrics.dcg_score(
                y_true=expected,
                y_pred=out,
                k=self.k,
                log_base=self.log_base,
                sample_weight=self.sample_weight,
                ignore_ties=self.ignore_ties,
            )
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Could not calculate score because of error: {e}",
            )
