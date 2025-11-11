# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv "$VIRTUAL_ENV"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        git \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip setuptools wheel \
    && pip install \
        colorama \
        exceptiongroup \
        iniconfig \
        packaging \
        pluggy<2,>=1.5 \
        pygments \
        tomli \
        argcomplete \
        attrs \
        hypothesis \
        mock \
        requests \
        xmlschema \
        PyYAML \
        numpy \
        pexpect \
        twisted \
        asynctest \
        pytest-xdist \
        py \
        pluggy@git+https://github.com/pytest-dev/pluggy.git \
        coverage \
    && pip install -e .

CMD ["pytest", "testing"]
