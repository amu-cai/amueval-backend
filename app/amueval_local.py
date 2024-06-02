import argparse
import pandas as pd

from metrics.metrics import Metrics

from typing import Any


def calculate(
    metric: str, out: list[Any], expected: list[Any], params: dict = {}
) -> float:
    metric = getattr(Metrics(), metric)
    metric_params = metric.model_fields.keys()

    if params is {}:
        return metric().calculate(expected, out)
    if set(params.keys()).issubset(set(metric_params)):
        return metric(**params).calculate(expected, out)
    else:
        print(
            f"Metric {metric} has the following params: {metric_params} and you gave those: {params}"
        )


def main():
    parser = argparse.ArgumentParser(
        description="AmuEval for local metrics calculation"
    )
    parser.add_argument(
        "-o",
        "--out",
        help="Path to or name of the file with values to check",
        required=True,
    )
    parser.add_argument(
        "-e",
        "--expected",
        help="Path to or name of the file with expected values",
        required=True,
    )
    parser.add_argument(
        "-m", "--metric", help="Name of the metric to use", required=True
    )
    parser.add_argument(
        "-mp",
        "--metric-parameters",
        help="Path to or name of the json file with parameters of the metric",
        required=False,
    )
    args = vars(parser.parse_args())

    out_values = pd.read_csv(args["out"])
    expected_values = pd.read_csv(args["expected"])
    print(calculate(args["metric"], out_values, expected_values))


if __name__ == "__main__":
    main()
