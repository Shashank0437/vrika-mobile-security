# Base image
FROM python:3.13-slim-bookworm

LABEL \
    name="Vrika Mobile Security" \
    author="Ajin Abraham <ajin25@gmail.com>" \
    maintainer="Ajin Abraham <ajin25@gmail.com>" \
    description="Vrika Mobile Security is an automated, all-in-one mobile application (Android/iOS/Windows) pen-testing, malware analysis and security assessment framework capable of performing static and dynamic analysis."

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    VRIKA_USER=vrika_mobile_security \
    USER_ID=9901 \
    VRIKA_PLATFORM=docker \
    VRIKA_ADB_BINARY=/usr/bin/adb \
    JAVA_HOME=/jdk-24.0.2 \
    PATH=/jdk-24.0.2/bin:/root/.local/bin:$PATH \
    DJANGO_SUPERUSER_USERNAME=vrika_mobile_security \
    DJANGO_SUPERUSER_PASSWORD=vrika_mobile_security

ARG TARGETPLATFORM

# Create vrika_mobile_security user and install system/Python dependencies in a single layer
COPY scripts/dependencies.sh vrika_mobile_security/Vrika/tools_download.py pyproject.toml poetry.lock ./
RUN groupadd --gid $USER_ID $VRIKA_USER && \
    useradd $VRIKA_USER --uid $USER_ID --gid $VRIKA_USER --create-home --home-dir /home/vrika_mobile_security --shell /bin/false && \
    apt-get update -y && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        android-sdk-build-tools \
        android-tools-adb \
        build-essential \
        curl \
        git \
        locales \
        python3-dev \
        sqlite3 \
        unzip \
        wget && \
    echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && \
    locale-gen en_US.UTF-8 && \
    update-locale LANG=en_US.UTF-8 && \
    ./dependencies.sh && \
    python3 -m pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only main --no-root --no-interaction --no-ansi && \
    poetry cache clear . --all --no-interaction && \
    python3 -m pip uninstall -y poetry poetry-core && \
    rm -f pyproject.toml poetry.lock && \
    chown -R $USER_ID:$USER_ID /home/vrika_mobile_security && \
    apt-get remove --purge -y \
        build-essential \
        git \
        python3-dev \
        wget && \
    apt-get autoremove --purge -y && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/* /tmp/* /root/.cache /root/.local

# Copy application source with final ownership to avoid a duplicate chown layer
WORKDIR /home/vrika_mobile_security/vrika-mobile-security
COPY --chown=$USER_ID:$USER_ID manage.py pyproject.toml ./
COPY --chown=$USER_ID:$USER_ID vrika_mobile_security ./vrika_mobile_security
COPY --chown=$USER_ID:$USER_ID scripts ./scripts

# Expose Vrika Mobile Security Port and Proxy Port
EXPOSE 8000 1337

# Switch to vrika_mobile_security user
USER $VRIKA_USER

# Run Vrika Mobile Security
CMD ["/home/vrika_mobile_security/vrika-mobile-security/scripts/entrypoint.sh"]
