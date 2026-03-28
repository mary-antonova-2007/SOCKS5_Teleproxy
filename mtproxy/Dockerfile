FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    ca-certificates curl git build-essential libssl-dev zlib1g-dev \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /opt

RUN git clone --depth 1 https://github.com/TelegramMessenger/MTProxy.git \
  && cd MTProxy \
  && make \
  && install -m 0755 objs/bin/mtproto-proxy /usr/local/bin/mtproto-proxy \
  && rm -rf /opt/MTProxy

COPY entrypoint.sh /usr/local/bin/mtproxy-entrypoint.sh
RUN chmod 0755 /usr/local/bin/mtproxy-entrypoint.sh

WORKDIR /opt/mtproxy

EXPOSE 443

CMD ["/usr/local/bin/mtproxy-entrypoint.sh"]
