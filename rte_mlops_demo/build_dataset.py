import yaml

import arrow
import pandas as pd
import tqdm

from rte_mlops_demo.scraper import QueryEnergyProduction, parse_response


def query_eco2mix_api(start_date, end_date, live=False) -> pd.DataFrame:
    results = []
    period_start_date = start_date
    while period_start_date < end_date:
        period_end_date = min(period_start_date.shift(months=1), end_date)
        query = QueryEnergyProduction(
            period_start_date, period_end_date, live_query=live
        )
        res = pd.DataFrame(parse_response(query.query_regional_production_live()))
        if not res.empty:
            results.append(res[["total_consumption", "region", "datetime"]])
        period_start_date = period_end_date
    return pd.concat(results)


def consolidated_data_is_complete(last_date_in_dataset, end_date):
    """For the dataset to be complete, it is expected that it contains consumption until 23:30 of the end date."""
    return last_date_in_dataset == end_date.shift(hours=23, minutes=30)


def is_half_hour_increment(datetime: str):
    datetime = arrow.get(datetime)
    return datetime.minute == 30 or datetime.minute == 0


if __name__ == "__main__":
    with open("params.yaml") as file:
        params = yaml.safe_load(file)["build_dataset"]

    start_date = arrow.get(params["start_date"])
    end_date = arrow.get(params["end_date"])

    # Start by querying the dataset on consolidated data
    df = query_eco2mix_api(start_date, end_date, live=False)
    max_consolidated_date = df.groupby("region")["datetime"].max().min()
    max_consolidated_date = arrow.get(max_consolidated_date)

    # Recent data missing have probably not been put in the consolidated dataset yet, so we query the live dataset
    if not consolidated_data_is_complete(max_consolidated_date, end_date):
        print(
            f"max date is {max_consolidated_date} instead of"
            f" {end_date.shift(hours=23, minutes=30)}, querying live data to build a complete dataset"
        )
        df_live = query_eco2mix_api(max_consolidated_date, end_date, live=True)
        # Live queries are on a 15 minutes basis instead of 30, keep only 30 minutes increment
        df_live = df_live.loc[df_live["datetime"].apply(is_half_hour_increment)]
        df = pd.concat([df, df_live]).drop_duplicates(["region", "datetime"])
    df.to_csv("data/raw_dataset.csv", index=False)
