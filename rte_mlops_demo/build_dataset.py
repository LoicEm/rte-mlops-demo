import yaml

import arrow
import pandas
import tqdm

from rte_mlops_demo.scraper import QueryEnergyProduction, parse_response


def query_eco2mix_api(start_date, end_date, live=False) -> pandas.DataFrame:
    query = QueryEnergyProduction(start_date, end_date, live_query=live)
    res = pandas.DataFrame(parse_response(query.query_regional_production_live()))
    return res[["total_consumption", "region", "datetime"]]


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

    QueryEnergyProduction(start_date, end_date, live_query=False)
    # Start by querying the dataset on consolidated data
    df = query_eco2mix_api(start_date, end_date, live=False)
    max_date = df.groupby("region")["datetime"].max().min()
    max_date = arrow.get(max_date)

    # Recent data missing have probably not been put in the consolidated dataset yet, so we query the live dataset
    if not consolidated_data_is_complete(max_date, end_date):
        print(
            f"max date is {max_date} instead of {end_date.shift(hours=23, minutes=30)}, querying live data to build a complete dataset"
        )
        df_live = query_eco2mix_api(max_date, end_date, live=True)
        # Live queries are on a 15 minutes basis instead of 30, keep only 30 minutes increment
        df_live = df_live.loc[df_live["datetime"].apply(is_half_hour_increment)]
        df = pandas.concat([df, df_live]).drop_duplicates(["region", "datetime"])
    df.to_csv("data/raw_dataset.csv", index=False)
