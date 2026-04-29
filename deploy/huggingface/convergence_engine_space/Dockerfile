FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV HF_HOME=/data/.huggingface

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    git \
    g++ \
    gcc \
    libgl1 \
    libglib2.0-0 \
    libsdl2-2.0-0 \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade pip \
    && python -m pip install \
        huggingface_hub \
        ipywidgets \
        jupyterlab \
        requests

WORKDIR /app

COPY start_server.sh /app/start_server.sh
COPY space_tools.py /app/space_tools.py
COPY README_RUNTIME.md /app/README_RUNTIME.md
COPY notebooks /app/notebooks
COPY jupyter-settings /app/jupyter-settings

RUN chmod +x /app/start_server.sh && mkdir -p /data

EXPOSE 7860

CMD ["/app/start_server.sh"]
