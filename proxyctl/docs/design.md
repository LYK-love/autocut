# Design

## Problem

`ssh -D` creates a local SOCKS proxy, but users still need to wire that proxy into desktop applications and terminal programs. macOS and Linux expose different desktop proxy configuration mechanisms, and terminal tools usually rely on environment variables instead.

## Goals

- Provide one CLI for setup, on, off, status, and shell environment output.
- Keep the implementation dependency-light and easy to audit.
- Avoid editing shell startup files automatically.
- Detect and explain common failure cases such as port conflicts and SSH connection failures.
- Support macOS and Linux backends without pretending to be a full VPN.

## Non-Goals

- Transparent proxying of all TCP or UDP traffic.
- Managing browser-specific proxy profiles.
- Supporting every Linux desktop environment in the first version.
- Running as a long-lived daemon.

## Architecture

`proxyctl` has four layers:

1. CLI command dispatch.
2. Persistent config and runtime state.
3. SSH tunnel lifecycle.
4. System proxy backend adapters.

The config file stores:

```text
SSH_DESTINATION
SOCKS_HOST
SOCKS_PORT
SYSTEM_BACKEND
SYSTEM_TARGET
```

Runtime state stores the SSH control socket and SSH log under:

```text
$XDG_STATE_HOME/proxyctl
```

or:

```text
~/.local/state/proxyctl
```

## Control Flow

`proxyctl on`:

1. Load config.
2. Check whether the SSH control socket is alive.
3. Check whether the local SOCKS port is already occupied.
4. Start SSH with `-M -S <socket> -f -N -D <host:port>`.
5. Enable the configured system proxy backend.

`proxyctl off`:

1. Load config.
2. Disable the configured system proxy backend.
3. Stop the SSH tunnel through the control socket.

## Backend Model

Each backend implements three operations:

- enable
- disable
- status

Current backend names:

- `macos`
- `gnome`
- `none`

`none` intentionally skips desktop proxy configuration. It is useful when another program, such as Clash Verge, owns system proxy settings and uses proxyctl's local SOCKS endpoint as one upstream proxy.

## Tradeoffs

Bash is used because the tool is mostly command orchestration around `ssh`, `networksetup`, and `gsettings`. A Rust implementation would be useful if the project grows a terminal UI, richer config validation, or background service management, but it would add build and distribution complexity for the current scope.
