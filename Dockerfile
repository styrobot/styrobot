FROM ubuntu:focal

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3 \
    python3-pip \
    git \
    libmagickwand-dev

RUN python3 -m pip install -U \
    discord.py \
    discord-py-slash-command \
    imagehash \
    Wand


WORKDIR /app/