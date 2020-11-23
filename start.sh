#!/bin/bash

if [[ -z "${O3API_LISTEN_IP}" ]]; then
    export O3API_LISTEN_IP='0.0.0.0'
fi

if [[ -z "${O3API_PORT}" ]]; then
    export O3API_PORT=5005
fi

if [[ -z "${O3API_TIMEOUT}" ]]; then
    export O3API_TIMEOUT=120
fi

if [[ -z "${O3API_WORKERS}" ]]; then
    export O3API_WORKERS=1
fi

if [ "${ENABLE_HTTPS}" == "True" ]; then
  if test -e /certs/cert.pem && test -f /certs/key.pem ; then
    exec gunicorn --bind $O3API_LISTEN_IP:$O3API_PORT -w "$O3API_WORKERS" \
    --certfile /certs/cert.pem --keyfile /certs/key.pem --timeout "$O3API_TIMEOUT"  o3api:app
  else
    echo "[ERROR] File /certs/cert.pem or /certs/key.pem NOT FOUND!"
    exit 1
  fi
else
  exec gunicorn --bind $O3API_LISTEN_IP:$O3API_PORT -w "$O3API_WORKERS" --timeout "$O3API_TIMEOUT"  o3api:app
fi
