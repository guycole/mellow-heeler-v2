#
# docker build --build-arg WOMBAT_UID=$(id -u wombat) --build-arg WOMBAT_GID=$(id -g wombat) -t heeler:latest .
# docker run -v /var/wombat:/mnt/wombat --name heeler heeler:latest
# docker run -e stuntbox=validator -v /var/wombat:/mnt/wombat --name heeler heeler:latest
# docker run -e stuntbox=koala --name heeler heeler:latest
#
FROM python:3.11-slim

WORKDIR /app

# Require wombat UID/GID to be provided by the Linux build host.
ARG WOMBAT_UID
ARG WOMBAT_GID

RUN set -eux; \
	test -n "${WOMBAT_UID}"; \
	test -n "${WOMBAT_GID}"

RUN printf '%s\n' '#!/bin/sh' 'set -eu' \
	'uid="${WOMBAT_UID:?WOMBAT_UID is required}"' \
	'gid="${WOMBAT_GID:?WOMBAT_GID is required}"' \
	'printf "WOMBAT_UID=%s\nWOMBAT_GID=%s\n" "$uid" "$gid" > /app/wombat_env.env' \
	> /usr/local/bin/collect-wombat-ids.sh \
	&& chmod +x /usr/local/bin/collect-wombat-ids.sh

ENV WOMBAT_UID=${WOMBAT_UID}
ENV WOMBAT_GID=${WOMBAT_GID}

RUN /usr/local/bin/collect-wombat-ids.sh

# Create and activate virtualenv first
RUN python -m venv /app/venv
ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy requirements and install them inside the venv
COPY requirements.txt ./
RUN $VIRTUAL_ENV/bin/pip install --no-cache-dir -r requirements.txt

COPY koala.py ./
COPY heeler_app.py ./
COPY postgres.py ./
COPY sql_table.py ./
COPY validator.py ./

RUN printf '%s\n' '#!/bin/sh' 'set -e' '/usr/local/bin/collect-wombat-ids.sh' 'set -a' '[ -f /app/wombat_env.env ] && . /app/wombat_env.env' 'set +a' 'exec "$@"' > /usr/local/bin/docker-entrypoint.sh \
	&& chmod +x /usr/local/bin/docker-entrypoint.sh

ENV FAILURE_DIR=/mnt/wombat/failure/
ENV FRESH_DIR=/mnt/wombat/fresh/heeler
ENV SUCCESS_DIR=/mnt/wombat/heeler/success/
ENV KOALA_DIR=/mnt/wombat/heeler/koala

ENV DB_CONN=postgresql+psycopg2://heeler_client:batabat@172.17.0.1:5432/heeler

RUN mkdir -p /mnt/wombat
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["python", "heeler_app.py"]
