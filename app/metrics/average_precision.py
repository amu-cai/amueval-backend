from sklearn import metrics as sk_metrics
from typing import Any
from fastapi import HTTPException
from metrics.metric_base import MetricBase


class AveragePrecision(MetricBase):
    """
    Average precision metric.

    Parameters
    ----------
    pos_label : int | float | bool | str, default 1
        The class to report if average='binary' and the data is binary.
    average : str | None, default 'macro'
        This parameter is required for multiclass/multilabel targets. Values:
        ‘micro’, ‘macro’, ‘samples’, ‘weighted’ or None.
    sample_weight : list[Any] | None, default None
        Sample weights.
    sorting: str, default "ascending"
        Information about the value of the metric.
    """

    pos_label: int | float | bool | str = 1
    average: str | None = "macro"
    sample_weight: list[Any] | None = None
    sorting: str = "ascending"

    def info(self) -> dict:
        return {
            "name": "average precision",
            "link": "https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html#sklearn.metrics.average_precision_score",
            "parameters": [
                {
                    "name": "pos_label",
                    "data_type": "int | float | bool | str",
                    "default_value": "1",
                },
                {
                    "name": "average",
                    "data_type": "str | None",
                    "default_value": "macro",
                    "possible_values": "micro, macro, samples, weighted",
                },
                {
                    "name": "sample_weight",
                    "data_type": "list[Any] | None",
                    "default_value": "None",
                },
            ],
        }

    def calculate(self, expected: list[Any], out: list[Any]) -> float:
        """
        Metric calculation

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
            return sk_metrics.average_precision_score(
                y_true=expected,
                y_pred=out,
                pos_label=self.pos_label,
                average=self.average,
                sample_weight=self.sample_weight,
            )
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Could not calculate score because of error: {e}",
            )
