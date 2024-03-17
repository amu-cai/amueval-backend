from pydantic import BaseModel
from typing import Any

from metric_base import MetricBase
from accuracy import Accuracy
from mse import MSE
from rmse import RMSE
from fbeta import FBeta
from recall import Recall
from precision import Precision
from average_precision import AveragePrecision
from balanced_accuracy import BalancedAccuracy
from brier import Brier
from cohen_kappa import CohenKappa
from dcg import DCG
from hamming_loss import HammingLoss
from hinge_loss import HingeLoss
from log_loss import LogLoss
from matthews_correlation import MatthewsCorrelation
from ndcg import NDCG
from explained_variance import ExplainedVariance
from median_absolute_error import MedianAbsoluteError
from r2 import R2
from mean_poisson_deviance import MeanPoissonDeviance
from mean_gamma_deviance import MeanGammaDeviance
from mean_tweedie_deviance import MeanTweedieDeviance
from d2_tweedie import D2Tweedie
from mean_pinball_loss import MeanPinballLoss


class Metrics(BaseModel):
    """All available metrics."""

    accuracy: MetricBase = Accuracy
    balanced_accuracy: MetricBase = BalancedAccuracy
    fbeta_score: MetricBase = FBeta
    rmse: MetricBase = RMSE
    mse: MetricBase = MSE
    recall: MetricBase = Recall
    precision: MetricBase = Precision
    average_precision: MetricBase = AveragePrecision
    brier: MetricBase = Brier
    cohen_kappa: MetricBase = CohenKappa
    dcg: MetricBase = DCG
    hamming_loss: MetricBase = HammingLoss
    hinge_loss: MetricBase = HingeLoss
    log_loss: MetricBase = LogLoss
    matthews_correlation: MetricBase = MatthewsCorrelation
    ndcg: MetricBase = NDCG
    explained_variance: MetricBase = ExplainedVariance
    median_absolute_error: MetricBase = MedianAbsoluteError
    r2: MetricBase = R2
    mean_poisson_deviance: MetricBase = MeanPoissonDeviance
    mean_gamma_deviance: MetricBase = MeanGammaDeviance
    mean_tweedie_deviance: MetricBase = MeanTweedieDeviance
    d2_tweedie: MetricBase = D2Tweedie
    mean_pinball_loss: MetricBase = MeanPinballLoss


def all_metrics() -> list[str]:
    """Show all available metrics."""
    return Metrics.model_fields.keys()


def metric_info(metric_name: str) -> dict:
    """Get information about a metric."""
    if metric_name not in all_metrics():
        print(f"Metric {metric_name} is not defined")
    else:
        metric = getattr(Metrics(), metric_name)
        return metric().info()


def calculate_default_metric(
    metric_name: str,
    expected: list[Any],
    out: list[Any],
) -> Any:
    """Use given metric with default settings."""
    if metric_name not in all_metrics():
        print(f"Metric {metric_name} is not defined")
    else:
        metric = getattr(Metrics(), metric_name)
        return metric().calculate(expected, out)


def calculate_metric(
    metric_name: str,
    expected: list[Any],
    out: list[Any],
    params: dict,
) -> Any:
    """Use given metric with non-default settings."""
    if metric_name not in all_metrics():
        print(f"Metric {metric_name} is not defined")
    else:
        metric = getattr(Metrics(), metric_name)
        metric_params = metric.model_fields.keys()

        if params == metric_params:
            return metric(**params).calculate(expected, out)
        else:
            print(f"Metric {metric_name} has the following params: {metric_params} and you gave those: {params}")
