FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/data/.huggingface \
    NLTK_DATA=/data/nltk_data \
    JUPYTER_CONFIG_DIR=/data/.jupyter \
    JUPYTER_RUNTIME_DIR=/data/.jupyter/runtime \
    JUPYTER_DATA_DIR=/data/.jupyter/data

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git \
        openssh-client \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir jupyterlab

RUN mkdir -p /etc/jupyter \
    && printf "%s\n" \
        "c.ServerApp.tornado_settings = {" \
        "    'headers': {" \
        "        'Content-Security-Policy': \"frame-ancestors 'self' https://huggingface.co https://*.huggingface.co\"" \
        "    }" \
        "}" \
        "c.ServerApp.cookie_options = {'SameSite': 'None', 'Secure': True}" \
        > /etc/jupyter/jupyter_server_config.py

WORKDIR /home/user

EXPOSE 7860

CMD ["sh", "-c", "set -eu; mkdir -p /data/.huggingface /data/.jupyter/runtime /data/.jupyter/data /data/nltk_data /data/work /home/user/.venvs; JUPYTER_PASSWORD_HASH=$(python -c 'from jupyter_server.auth import passwd; import os; print(passwd(os.environ.get(\"JUPYTER_TOKEN\") or \"techlady\"))'); cd /data/work; exec jupyter lab --ip 0.0.0.0 --port 7860 --IdentityProvider.token='' --PasswordIdentityProvider.hashed_password=\"$JUPYTER_PASSWORD_HASH\" --PasswordIdentityProvider.password_required=True --PasswordIdentityProvider.allow_password_change=False --ServerApp.allow_origin='*' --ServerApp.root_dir=/data/work --ServerApp.trust_xheaders=True --ServerApp.disable_check_xsrf=True --no-browser --allow-root"]
