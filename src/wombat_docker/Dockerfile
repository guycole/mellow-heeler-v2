#
# Build from the src/ directory (one level above this file):
# docker build -f wombat_docker/Dockerfile -t wombat:latest .
# docker run -e WOMBAT_UID=<uid> -e WOMBAT_GID=<gid> -v /var/wombat:/mnt/wombat --name wombat wombat:latest
# docker run -e stuntbox=validator -e WOMBAT_UID=<uid> -e WOMBAT_GID=<gid> -v /var/wombat:/mnt/wombat --name wombat wombat:latest
# docker run -e stuntbox=koala -e WOMBAT_UID=<uid> -e WOMBAT_GID=<gid> --name wombat wombat:latest
#
FROM python:3.11-slim

WORKDIR /app

# Create and activate virtualenv first
RUN python -m venv /app/venv
ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy requirements and install them inside the venv
COPY wombat_docker/requirements.txt ./
RUN $VIRTUAL_ENV/bin/pip install --no-cache-dir -r requirements.txt

COPY helper/ ./helper/
COPY wombat_docker/heeler_app.py ./
COPY wombat_docker/koala.py ./
COPY wombat_docker/validator.py ./

RUN printf '%s\n' '#!/bin/sh' 'set -eu' \
	': "${WOMBAT_UID:?WOMBAT_UID is required}"' \
	': "${WOMBAT_GID:?WOMBAT_GID is required}"' \
	'exec "$@"' > /usr/local/bin/docker-entrypoint.sh \
	&& chmod +x /usr/local/bin/docker-entrypoint.sh

ENV FAILURE_DIR=/mnt/wombat/failure
ENV FRESH_DIR=/mnt/wombat/fresh/heeler
ENV KOALA_DIR=/mnt/wombat/heeler/koala
ENV SUCCESS_DIR=/mnt/wombat/heeler/success

# wombat gateway
ENV DB_CONN=postgresql+psycopg2://heeler_client:batabat@172.17.0.1:5432/heeler

RUN mkdir -p /mnt/wombat
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["python", "heeler_app.py"]
