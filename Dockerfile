FROM python:3.8

WORKDIR /code

ENV POETRY_VERSION "1.1.12"
RUN pip install "poetry==$POETRY_VERSION"
RUN poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock  /code/

RUN poetry install --no-dev

ENV MODEL_PATH /models/model.joblib
COPY models/model.joblib /models/model.joblib

COPY rte_mlops_demo /code/rte_mlops_demo

ENTRYPOINT [ "uvicorn", "rte_mlops_demo.api:app", "--host", "0.0.0.0",  "--port", "8000"]