FROM ubuntu:focal

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3 \
    python3-pip \
    git

RUN python3 -m pip install -U \
    discord.py

WORKDIR /app/