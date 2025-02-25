import json

from pydantic import BaseModel
from typing import Any
from fastapi import HTTPException

from metrics.metric_base import MetricBase
from metrics.accuracy import Accuracy
from metrics.average_precision import AveragePrecision
from metrics.balanced_accuracy import BalancedAccuracy
from metrics.bleu import Bleu
from metrics.brier import Brier
from metrics.cer import CER
from metrics.cohen_kappa import CohenKappa
from metrics.d2_absolute_error import D2AbsoluteError
from metrics.d2_pinball import D2Pinball
from metrics.d2_tweedie import D2Tweedie
from metrics.dcg import DCG
from metrics.explained_variance import ExplainedVariance
from metrics.f1_score import F1
from metrics.fbeta import FBeta
from metrics.hamming_loss import HammingLoss
from metrics.hinge_loss import HingeLoss
from metrics.log_loss import LogLoss
from metrics.matthews_correlation import MatthewsCorrelation
from metrics.mean_absolute_error import MeanAbsoluteError
from metrics.mean_absolute_percentage_error import MeanAbsolutePercentageError
from metrics.mean_gamma_deviance import MeanGammaDeviance
from metrics.mean_pinball_loss import MeanPinballLoss
from metrics.mean_poisson_deviance import MeanPoissonDeviance
from metrics.mean_tweedie_deviance import MeanTweedieDeviance
from metrics.median_absolute_error import MedianAbsoluteError
from metrics.mse import MSE
from metrics.ndcg import NDCG
from metrics.precision import Precision
from metrics.r2 import R2
from metrics.recall import Recall
from metrics.rmse import RMSE
from metrics.wer import WER
from metrics.precision_string import PrecisionString
from metrics.recall_string import RecallString
from metrics.f1_score_string import F1String
from metrics.fbeta_gec import FBetaGEC


class Metrics(BaseModel):
    """All available metrics."""

    accuracy: MetricBase = Accuracy
    average_precision: MetricBase = AveragePrecision
    balanced_accuracy: MetricBase = BalancedAccuracy
    bleu: MetricBase = Bleu
    brier: MetricBase = Brier
    cer: MetricBase = CER
    cohen_kappa: MetricBase = CohenKappa
    d2_absolute_error: MetricBase = D2AbsoluteError
    d2_pinball: MetricBase = D2Pinball
    d2_tweedie: MetricBase = D2Tweedie
    dcg: MetricBase = DCG
    explained_variance: MetricBase = ExplainedVariance
    f1_score: MetricBase = F1
    fbeta_score: MetricBase = FBeta
    hamming_loss: MetricBase = HammingLoss
    hinge_loss: MetricBase = HingeLoss
    log_loss: MetricBase = LogLoss
    matthews_correlation: MetricBase = MatthewsCorrelation
    mean_absolute_error: MetricBase = MeanAbsoluteError
    mean_absolute_percentage_error: MetricBase = MeanAbsolutePercentageError
    mean_gamma_deviance: MetricBase = MeanGammaDeviance
    mean_pinball_loss: MetricBase = MeanPinballLoss
    mean_poisson_deviance: MetricBase = MeanPoissonDeviance
    mean_tweedie_deviance: MetricBase = MeanTweedieDeviance
    median_absolute_error: MetricBase = MedianAbsoluteError
    mse: MetricBase = MSE
    ndcg: MetricBase = NDCG
    precision: MetricBase = Precision
    r2: MetricBase = R2
    recall: MetricBase = Recall
    rmse: MetricBase = RMSE
    wer: MetricBase = WER
    f1_string: MetricBase = F1String
    recall_string: MetricBase = RecallString
    precision_string: MetricBase = PrecisionString
    fbeta_gec: MetricBase = FBetaGEC
    

def all_metrics() -> list[str]:
    """Show all available metrics."""
    return Metrics.model_fields.keys()


def metric_info(metric_name: str) -> dict[str, Any]:
    """Get information about a metric."""
    if metric_name not in all_metrics():
        raise HTTPException(
            status_code=422, detail=f"Metric {metric_name} is not defined"
        )
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
        raise HTTPException(
            status_code=422, detail=f"Metric {metric_name} is not defined"
        )
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
        raise HTTPException(
            status_code=422, detail=f"Metric {metric_name} is not defined"
        )

    metric = getattr(Metrics(), metric_name)
    metric_params = metric.model_fields.keys()

    # When getting params from db as json string, `None` values are read as
    # string `"None"`, which causes errors, when params are given to the metric
    # calculation function. This bit of code is to replace all string `"None"`
    # with `None` values.
    clean_params = dict()
    for key, value in params.items():
        if value == "None":
            value = None

        clean_params[key] = value

    if set(clean_params.keys()).issubset(set(metric_params)):
        return metric(**clean_params).calculate(expected, out)
    else:
        detail_info = f"Metric {metric_name} has the following params: {
            metric_params} and you gave those: {clean_params}"
        raise HTTPException(status_code=422, detail=detail_info)


def str2metric(str_metric: str) -> MetricBase:
    """Convert a json as string containing metric and its parameters into metric."""
    json_metric = json.loads(str_metric)
    metric_name = json_metric["name"]
    params = json_metric["params"]

    if metric_name not in all_metrics():
        raise HTTPException(
            status_code=422, detail=f"Metric {metric_name} is not defined"
        )
    else:
        metric = getattr(Metrics(), metric_name)
        metric_params = metric.model_fields.keys()

        if set(params.keys()).issubset(set(metric_params)):
            return metric(**params)
        else:
            detail_info = f"Metric {metric_name} has the following params: {
                metric_params} and you gave those: {params}"
            raise HTTPException(status_code=422, detail=detail_info)
