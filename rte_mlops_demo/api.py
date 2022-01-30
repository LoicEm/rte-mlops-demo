import logging
import os
import pathlib

import arrow
from fastapi import FastAPI
import joblib
import pandas as pd
from rte_mlops_demo.build_dataset import is_half_hour_increment

from rte_mlops_demo.scraper import QueryEnergyProduction, parse_response

app = FastAPI()
logger = logging.getLogger(__name__)

MODEL_PATH = os.environ.get("MODEL_PATH")
model = joblib.load(MODEL_PATH)


@app.get("/")
async def root():
    return "Hello World"


@app.get("/predict/{prediction_date}")
async def predict(prediction_date: str):
    prediction_date = arrow.get(prediction_date)
    logger.debug(f"querying data for {prediction_date}")
    # Get the data from the day before
    daily_data = get_data(prediction_date)
    # Make the prediction based on this data
    model.update(daily_data, update_params=False)
    prediction = model.predict([i for i in range(1, 49)])["total_consumption"].to_dict()
    prediction = {k.start_time.isoformat(): v for k, v in prediction.items()}
    return prediction


def get_data(date: arrow.Arrow):
    query = QueryEnergyProduction(date.shift(days=-1), date)
    df = pd.DataFrame(parse_response(query.query_regional_production_live()))
    df = df.loc[
        df["datetime"].apply(is_half_hour_increment), ["total_consumption", "datetime"]
    ].sort_values("datetime")
    df["datetime"] = pd.PeriodIndex(pd.to_datetime(df["datetime"]), freq="30min")
    df = df.set_index("datetime")
    return df
