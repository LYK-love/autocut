# CLI Reference

## Commands

```bash
proxyctl setup
proxyctl on
proxyctl off
proxyctl restart
proxyctl status
proxyctl env
proxyctl unenv
proxyctl help
```

## `setup`

Interactive configuration. It writes a config file to:

```text
$XDG_CONFIG_HOME/proxyctl/config
```

or, when `XDG_CONFIG_HOME` is unset:

```text
~/.config/proxyctl/config
```

The setup flow asks for:

- SSH destination
- local SOCKS bind address
- local SOCKS port
- system proxy backend
- backend-specific target, such as a macOS network service

## `on`

Starts the SSH SOCKS tunnel and then enables the configured system proxy backend.

Equivalent SSH shape:

```bash
ssh -N -D 127.0.0.1:7899 user@example.com
```

The real command also uses an SSH control socket so `proxyctl off` can stop the tunnel.

## `off`

Disables the configured system proxy backend and stops the SSH tunnel when proxyctl owns it.

This command cannot unset environment variables in an already-running parent shell. Use:

```bash
eval "$(proxyctl unenv)"
```

## `env`

Prints shell exports for the current SOCKS endpoint:

```bash
eval "$(proxyctl env)"
```

The generated proxy URL uses `socks5h://` so DNS resolution is delegated to the SOCKS proxy for tools that support it.

## `status`

Shows:

- saved config
- SSH tunnel status
- local port status
- system proxy backend status

## Backends

macOS uses:

```bash
networksetup -setsocksfirewallproxy
networksetup -setsocksfirewallproxystate
```

macOS also supports backend `none`. Use it when another tool, such as Clash Verge, owns the system proxy and only needs proxyctl's local SOCKS endpoint as an upstream proxy.

Linux GNOME uses:

```bash
gsettings set org.gnome.system.proxy.socks host
gsettings set org.gnome.system.proxy.socks port
gsettings set org.gnome.system.proxy mode manual
```
