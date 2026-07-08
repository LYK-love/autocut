# Workflows

## First-Time macOS Setup

```bash
proxyctl setup
```

Choose:

- SSH destination: for example `user@example.com`
- local SOCKS address: usually `127.0.0.1`
- local SOCKS port: usually `7899`
- macOS network service: usually `Wi-Fi`

List macOS network services manually:

```bash
networksetup -listallnetworkservices
```

## First-Time Linux GNOME Setup

```bash
proxyctl setup
```

Choose:

- SSH destination: for example `user@example.com`
- local SOCKS address: usually `127.0.0.1`
- local SOCKS port: usually `7899`
- Linux system proxy backend: `gnome`

If `gsettings` is unavailable, choose `none` and use terminal environment variables.

## Daily Use

Start the proxy:

```bash
proxyctl on
```

Use the proxy in the current shell:

```bash
eval "$(proxyctl env)"
```

Check state:

```bash
proxyctl status
```

Stop the proxy:

```bash
proxyctl off
```

Unset shell variables:

```bash
eval "$(proxyctl unenv)"
```

## Clash Verge Split Routing

When Clash Verge owns the system proxy, configure `proxyctl` with backend `none`.

```bash
proxyctl setup
```

Choose:

- system proxy backend: `none`

Then start only the local SSH SOCKS endpoint:

```bash
proxyctl on
```

Add this endpoint to Clash Verge as a SOCKS5 proxy:

```yaml
proxies:
  - name: SSH-SOCKS
    type: socks5
    server: 127.0.0.1
    port: 7899
```

Let Clash rules decide which sites use `SSH-SOCKS` and which sites use `DIRECT`.

## Troubleshooting

If the local port is already in use, run:

```bash
proxyctl status
```

Then either stop the old process or rerun:

```bash
proxyctl setup
```

and choose another local SOCKS port.

If SSH cannot connect, test manually:

```bash
ssh user@example.com
ssh -N -D 127.0.0.1:7899 user@example.com
```

The SSH log path is printed in the error output.
