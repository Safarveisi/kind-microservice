FROM python:3.10-slim AS requirements-stage 

WORKDIR /tmp

RUN pip install poetry

COPY ./pyproject.toml ./poetry.lock ./microservice ./

RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM python:3.10-slim

ENV user=developer

RUN useradd -m -d /home/${user} ${user} && \
    chown -R ${user} /home/${user}

USER ${user}
WORKDIR /home/${user}

ENV PATH=/home/${user}/.local/bin:$PATH
ENV RAY_DEDUP_LOGS=0

COPY --from=requirements-stage /tmp/ .

EXPOSE 8000

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt 

ENTRYPOINT ["python", "app.py"]