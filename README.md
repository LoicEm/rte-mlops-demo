# Quickly building and serving a model using DVC and Docker

This repository is a quick demonstration showing how to quickly iterate in the development of a machine learning model aiming at predicting electric consumption over 24 hours in Ile-de-France.

The data is collected on the [rte-eco2mix API](https://opendata.reseaux-energies.fr/explore/dataset/eco2mix-regional-tr/information/?disjunctive.libelle_region&disjunctive.nature).

## Prerequisites

I recommend installing the dependencies through [Poetry](https://python-poetry.org), but a `requirements.txt` file is provided for an install via pip.

[Docker](https://docs.docker.com/get-docker/) must also be installed to run and build the serving containers.

(If the poetry option is selected, then all the commands must be preceded by `poetry run`.)

## Running the experiment

The `dvc.yaml` describes the stages of the pipeline. To reproduce them, simply run

`dvc exp run`

As the external API can return slightly different data over time, it might be possible that the results of the pipeline will also differ (Ideally, a [dvc remote storage](https://dvc.org/doc/use-cases/sharing-data-and-model-files) would enable to have the exact same data everytime).

In this case, you will commit the results of your first run and work from there.

### Comparing the results with other experiments

At the moment, only the [MAPE](https://en.wikipedia.org/wiki/Mean_absolute_percentage_error) metric is used. 

You can compare your results with the historical experiments by running the [dvc exp show](https://dvc.org/doc/command-reference/exp/show#-T) command:

```
dvc exp show -T
```


## Building a serving container

To serve the model, I use [Docker containers](https://www.docker.com/), which ensures that all dependencies are  present inside of an image, and makes it easy to run it locally or on a remote system.

An image is ready to use, you can pull it by running:

```
docker pull ghcr.io/loicem/rte-mlops-demo:arima_model
```

### Running an image locally

Once you have pulled (or built) an image, you can run it using:

```
docker run -p 8000:8000 ghcr.io/loicem/rte-mlops-demo:arima_model
```

The API will then be available on `localhost:8000`

### Building a custom image

Once you have produced a model that looks better, you can create a custom docker image containing it.

Just run:

```
docker build . -t <your tag>
```