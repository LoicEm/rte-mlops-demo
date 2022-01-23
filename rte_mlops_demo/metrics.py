import numpy as np
from sktime.performance_metrics.forecasting import make_forecasting_scorer


def mean_absolute_percentage_error(
    y_truth: np.array, y_pred: np.array, multioutput: str
):
    metrics_dict = {
        "uniform_average": np.mean(np.abs((y_truth - np.ceil(y_pred)) / y_truth)),
        "raw_values": np.abs((y_truth - np.ceil(y_pred)) / y_truth),
    }
    try:
        return metrics_dict[multioutput]
    except KeyError:
        print(
            "multioutput not specified correctly - "
            "pick `raw_values` or `uniform_average`"
        )

    return np.mean(np.abs((y_truth - np.ceil(y_pred)) / y_truth))


fc_mape = make_forecasting_scorer(mean_absolute_percentage_error)
