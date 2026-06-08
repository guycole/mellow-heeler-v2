#
# docker build -t heeler:latest .
# docker run -v /var/wombat:/mnt/wombat --name heeler heeler:latest
# docker run -e stuntbox=validate -v /var/wombat:/mnt/wombat --name heeler heeler:latest
# docker run -e stuntbox=score -e limit=5 --name heeler heeler:latest
# docker run -e stuntbox=score --name heeler heeler:latest
#
FROM python:3.11-slim

WORKDIR /app

# Ensure wombat exists, then persist its UID/GID discovered at build time.
RUN set -eux; \
	if ! id -u wombat >/dev/null 2>&1; then \
		addgroup --system wombat; \
		adduser --system --ingroup wombat wombat; \
	fi; \
	uid="$(id -u wombat)"; \
	gid="$(id -g wombat)"; \
	printf 'export WOMBAT_UID=%s\nexport WOMBAT_GID=%s\n' "$uid" "$gid" > /app/wombat_env.sh

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
COPY scorer.py ./
COPY sql_table.py ./
COPY validator.py ./

RUN printf '%s\n' '#!/bin/sh' 'set -e' '[ -f /app/wombat_env.sh ] && . /app/wombat_env.sh' 'exec "$@"' > /usr/local/bin/docker-entrypoint.sh \
	&& chmod +x /usr/local/bin/docker-entrypoint.sh

RUN mkdir -p /mnt/wombat
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["python", "heeler_app.py"]
