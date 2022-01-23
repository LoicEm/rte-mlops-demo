"""Train the module and get the useful metrics."""
import json

import numpy as np
import pandas as pd
import sktime

from sktime.datasets import load_airline
from sktime.forecasting.model_selection import temporal_train_test_split
from sktime.forecasting.naive import NaiveForecaster

from rte_mlops_demo.metrics import fc_mape


def build_training_metrics(y_test, y_pred):
    return {"MAPE": fc_mape(y_test, y_pred)}


def save_metrics(metrics: dict):
    with open("metrics.yaml", "w") as file:
        json.dump(metrics, file)


if __name__ == "__main__":
    # Read the data
    df = pd.read_csv("data/raw_dataset.csv")
    df["datetime"] = pd.PeriodIndex(pd.to_datetime(df["datetime"]), freq="30min")
    y = df.set_index("datetime")["total_consumption"]

    # Predict for 24 hours (48 30-minute periods)
    forecast_horizon = np.arange(1, 49)

    # Create a test set of 7 days
    y_train, y_test = temporal_train_test_split(y, test_size=2 * 24 * 7)
    forecaster = NaiveForecaster()
    forecaster.fit(y_train)
    y_pred = forecaster.predict(np.arange(1, y_test.size + 1))

    test_metrics = build_training_metrics(y_test, y_pred)

    save_metrics(test_metrics)
