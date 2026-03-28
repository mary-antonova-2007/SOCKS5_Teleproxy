# telegram-socks5-proxy

This directory contains the proxy-side runtime for the Telegram SOCKS5 service.

## Runtime contract

- Config file: `/data/3proxy.cfg`
- Users file: `/data/users.conf`
- Pidfile: `/data/3proxy.pid`
- Log file: `/data/3proxy.log`

The container boots with a generated default config if `/data/3proxy.cfg` is missing. Backend code is expected to keep the same paths and update the active config atomically, then signal the PID from `/data/3proxy.pid` with `SIGHUP`.

## Environment

- `SOCKS5_PORT` - listening port, default `1080`
- `PROXY_BIND_ADDRESS` - bind address, default `0.0.0.0`
- `PROXY_PRIMARY_RESOLVER` - primary DNS server, default `1.1.1.1`
- `PROXY_SECONDARY_RESOLVER` - fallback DNS server, default `8.8.8.8`
- `PROXY_DATA_DIR` - shared data directory, default `/data`
- `PROXY_CONFIG_PATH` - active config path, default `/data/3proxy.cfg`
- `PROXY_USERS_CONF_PATH` - users include path, default `/data/users.conf`
- `PROXY_PIDFILE_PATH` - pidfile path, default `/data/3proxy.pid`
- `PROXY_LOG_PATH` - log path, default `/data/3proxy.log`

## Integration notes

- Backend should keep `users.conf` in sync with the JSON user store.
- Backend should regenerate `3proxy.cfg` atomically and keep `pidfile`, `monitor`, `auth strong`, and `socks` lines intact.
- The container healthcheck only verifies that the PID in the pidfile is alive.
