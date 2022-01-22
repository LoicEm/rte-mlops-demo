import logging
import os

import arrow
import requests
import yaml

logger = logging.getLogger(__name__)

API_URL = "https://opendata.reseaux-energies.fr/api/records/1.0/search/"

LIVE_DATASET = "eco2mix-regional-tr"
CONSOLIDATED_DATASET = "eco2mix-regional-cons-def"

RECORDS_PARSING_CONFIG = os.path.join(os.path.dirname(__file__), "parser_config.yaml")


class QueryEnergyProduction:
    def __init__(
        self,
        start_datetime: arrow.Arrow,
        end_datetime: arrow.Arrow,
        live_query: bool = True,
    ):
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.live_query = live_query

        self._n_hits = None

    def query_regional_production_live(self):
        """Query regional data on production on the past day.
        This will create duplicates."""
        params = self.get_query_params(n_rows=self._n_hits)
        res = requests.get(API_URL, params=params)

        yield from res.json()["records"]

    def get_query_params(self, n_rows: int):
        query_datetime = get_datetime_query_param(
            self.start_datetime, self.end_datetime
        )
        if self.live_query:
            dataset = LIVE_DATASET
        else:
            dataset = CONSOLIDATED_DATASET
        params = {
            "dataset": dataset,
            "q": query_datetime,
            "rows": n_rows,
            "refine.code_insee_region": "11",  # Query only Ile-de-France
        }
        return params

    @property
    def n_hits(self):
        if self._n_hits is None:
            self._n_hits = self.query_n_hits()
        return self._n_hits

    def query_n_hits(self):
        params = self.get_query_params(n_rows=0)
        logger.debug(f"Getting number of hits on period {params['q']}")
        res = requests.get(API_URL, params=params).json()
        n_hits = res["nhits"]
        if n_hits > 10_000:
            raise ValueError(
                "No more than 10 000 rows can be queried at once, please refine you query"
            )


def get_datetime_query_param(start_datetime, end_datetime) -> str:
    end = end_datetime.format("YYYY-MM-DDTHH:mm")
    start = start_datetime.format("YYYY-MM-DDTHH:mm")
    return f"date_heure:[{start} TO {end}]"


def parse_response(records, on_keyerror="raise"):
    for record in records:
        try:
            yield RecordParser(record).parse()
        except KeyError as err:
            logger.warning(f"Error for record {record.get('recordid')}: {err}")
            if on_keyerror == "raise":
                raise err


class RecordParser:
    def __init__(self, record: dict, config_path: str = RECORDS_PARSING_CONFIG):

        self.record = record
        self.config_path = config_path

        with open(self.config_path) as file:
            self.config = yaml.safe_load(file)

    def parse(self) -> dict:
        consumption = self.parse_consumption()
        production = self.parse_production()
        fluxes = self.parse_flux()
        return {
            "total_consumption": consumption,
            "production": production,
            "flux": fluxes,
            "region_code": self.record["fields"]["code_insee_region"],
            "dataset_id": self.record["datasetid"],
            "record_id": self.record["recordid"],
            "region": self.record["fields"]["libelle_region"],
            "datetime": self.record["fields"]["date_heure"],
        }

    def parse_consumption(self):
        consumption_key = self.config["consumption"]
        return self.record["fields"].get(consumption_key)

    def parse_production(self):
        production_keys = self.config["production_types"]
        return {
            production_key: self.record["fields"].get(production_key)
            for production_key in production_keys
        }

    def parse_flux(self):
        flux_prefix = self.config["flux_prefix"]
        return {
            k: self.parse_flux_value(v)
            for k, v in self.record["fields"].items()
            if k.startswith(flux_prefix)
        }

    @staticmethod
    def parse_flux_value(flux_value):
        if flux_value == "-":
            return 0
        else:
            return flux_value
