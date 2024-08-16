from sklearn import metrics as sk_metrics
from typing import Any
from fastapi import HTTPException
from metrics.metric_base import MetricBase


class LogLoss(MetricBase):
    """
    Log loss metric class.

    Parameters
    ----------
    eps : float | str, default "auto"
        The default value changed from 1e-15 to "auto" that is equivalent to
        np.finfo(y_pred.dtype).eps.
    normalize : bool, default True
        If true, return the mean loss per sample. Otherwise, return the sum of
        the per-sample losses.
    sample_weight : list[Any] | None, default None
        Sample weights.
    labels : list[Any] | None, default None
        If not provided, labels will be inferred from expected.
    sorting: str, default "descending"
        Information about the value of the metric.
    """

    eps: float | str = "auto"
    normalize: bool = True
    sample_weight: list[Any] | None = None
    labels: list[Any] | None = None
    sorting: str = "descending"

    def info(self) -> dict:
        return {
            "name": "Log loss",
            "link": "https://scikit-learn.org/stable/modules/generated/sklearn.metrics.log_loss.html#sklearn.metrics.log_loss",
            "parameters": [
                {"name": "eps", "data_type": "float | str", "default_value": "auto"},
                {"name": "normalize", "data_type": "bool", "default_value": "True"},
                {
                    "name": "sample_weight",
                    "data_type": "list[Any] | None",
                    "default_value": "None",
                },
                {
                    "name": "labels",
                    "data_type": "list[Any] | None",
                    "default_value": "None",
                },
            ],
        }

    def calculate(
        self,
        expected: list[Any],
        out: list[Any],
    ) -> float:
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
            return sk_metrics.log_loss(
                y_true=expected,
                y_pred=out,
                eps=self.eps,
                normalize=self.normalize,
                sample_weight=self.sample_weight,
                labels=self.labels,
            )
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Could not calculate score because of error: {e}",
            )
