FROM 3proxy/3proxy:latest

USER root

ENV DATA_DIR=/data \
    SOCKS5_PROXY_CONFIG_FILE=/data/3proxy.cfg \
    SOCKS5_PROXY_PID_FILE=/data/3proxy.pid \
    SOCKS5_PROXY_LOG_FILE=/data/3proxy.log \
    SOCKS5_PROXY_RELOAD_REQUEST_FILE=/data/reload.request \
    SOCKS5_PROXY_RELOAD_STATUS_FILE=/data/reload.status \
    PROXY_TEMPLATE_PATH=/usr/local/share/telegram-socks5-proxy/3proxy.cfg.tpl \
    PROXY_SERVICE_NAME=telegram-socks5-proxy \
    SOCKS5_PORT=1080 \
    PROXY_BIND_ADDRESS=0.0.0.0 \
    PROXY_PRIMARY_RESOLVER=1.1.1.1 \
    PROXY_SECONDARY_RESOLVER=8.8.8.8

RUN mkdir -p /usr/local/bin /usr/local/share/telegram-socks5-proxy /data

COPY entrypoint.sh /usr/local/bin/telegram-socks5-entrypoint.sh
COPY 3proxy.cfg.tpl /usr/local/share/telegram-socks5-proxy/3proxy.cfg.tpl

RUN chmod 0755 /usr/local/bin/telegram-socks5-entrypoint.sh

VOLUME ["/data"]

EXPOSE 1080/tcp

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD sh -eu -c 'pidfile="${SOCKS5_PROXY_PID_FILE:-/data/3proxy.pid}"; test -s "$pidfile" && kill -0 "$(cat "$pidfile")"'

ENTRYPOINT ["/bin/sh", "/usr/local/bin/telegram-socks5-entrypoint.sh"]
