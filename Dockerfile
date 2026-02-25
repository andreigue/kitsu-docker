FROM ubuntu:jammy

ENV DEBIAN_FRONTEND=noninteractive
ENV PG_VERSION=14
ENV DB_USERNAME=root DB_HOST=
# https://github.com/cgwire/zou/tags
ARG ZOU_VERSION=v0.20.76
# https://github.com/cgwire/kitsu/tags
ARG KITSU_VERSION=v0.20.94

USER root

# hadolint ignore=DL3008
RUN mkdir -p /opt/zou/zou /var/log/zou /opt/zou/previews && \
    apt-get update && \
    apt-get install --no-install-recommends -q -y \
    bzip2 \
    build-essential \
    dos2unix \
    ffmpeg \
    git \
    gcc \
    nginx \
    postgresql \
    postgresql-client \
    python3 \
    python3-dev \
    python3-pip \
    python3-venv \
    libjpeg-dev \
    libpq-dev \
    redis-server \
    software-properties-common \
    supervisor \
    xmlsec1 \
    wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create database
USER postgres

# hadolint ignore=DL3001
RUN service postgresql start && \
    createuser root && createdb -T template0 -E UTF8 --owner root root && \
    createdb -T template0 -E UTF8 --owner root zoudb && \
    service postgresql stop

# hadolint ignore=DL3002
USER root

# Wait for the startup or shutdown to complete
COPY --chown=postgres:postgres --chmod=0644 ./kitsu-docker/docker/pg_ctl.conf /etc/postgresql/${PG_VERSION}/main/pg_ctl.conf
COPY --chown=postgres:postgres --chmod=0644 ./kitsu-docker/docker/postgresql-log.conf /etc/postgresql/${PG_VERSION}/main/conf.d/postgresql-log.conf
# hadolint ignore=DL3013
RUN sed -i "s/bind .*/bind 127.0.0.1/g" /etc/redis/redis.conf && \
    git config --global --add advice.detachedHead false && \
    mkdir -p /opt/zou/kitsu && \
    python3 -m venv /opt/zou/env && \
    /opt/zou/env/bin/pip install --no-cache-dir --upgrade pip wheel "setuptools<70" && \
    # Clone Zou source code instead of installing package
    cd /opt/zou && \
    git clone --branch ${ZOU_VERSION} https://github.com/cgwire/zou.git zou-src && \
    cd zou-src && \
    /opt/zou/env/bin/pip install --no-cache-dir --no-build-isolation -e . && \

    cd .. && \
    /opt/zou/env/bin/pip install --no-cache-dir sendria && \
    rm /etc/nginx/sites-enabled/default

# Copy local kitsu frontend
COPY kitsu /opt/zou/kitsu

WORKDIR /opt/zou

COPY ./kitsu-docker/docker/gunicorn.py /etc/zou/gunicorn.py
COPY ./kitsu-docker/docker/gunicorn-events.py /etc/zou/gunicorn-events.py
COPY ./kitsu-docker/docker/nginx.conf /etc/nginx/sites-enabled/zou
COPY kitsu-docker/docker/supervisord.conf /etc/supervisord.conf
COPY --chmod=0755 ./kitsu-docker/docker/init_zou.sh /opt/zou/
COPY --chmod=0755 ./kitsu-docker/docker/start_zou.sh /opt/zou/

# Convert Windows line endings to Unix
RUN dos2unix /opt/zou/init_zou.sh /opt/zou/start_zou.sh

RUN echo Initialising Zou... && \
    /opt/zou/init_zou.sh

# Patch the Person model with Telegram fields (after Zou is initialized)
RUN /opt/zou/env/bin/python /opt/zou/docker/patch_zou.py

EXPOSE 80
EXPOSE 1080
VOLUME ["/var/lib/postgresql", "/opt/zou/previews"]
CMD ["/opt/zou/start_zou.sh"]
