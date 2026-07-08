# proxyctl
> You can use AI to translate or explain this document and the rest of the project's documentation in your preferred language.
>
> 你可以使用 AI 将本文档和本项目的其他文档翻译成你偏好的语言，或为你解读其中的内容。

`proxyctl` is a small Bash CLI for turning an SSH dynamic SOCKS proxy into a usable desktop and terminal proxy.

It starts an SSH tunnel with `ssh -D`, enables a supported system proxy backend, and prints optional proxy environment variables for terminal programs. It is intentionally not a VPN or transparent packet router: applications must either respect the desktop proxy settings or the shell environment variables.

Supported system proxy backends:

| OS | Backend | Status |
| --- | --- | --- |
| macOS | `networksetup` SOCKS proxy | Supported |
| macOS | `none` | Supported |
| Linux | GNOME `gsettings` proxy | Supported |
| Linux | Other desktops | Use `none` backend plus `proxyctl env` |

## Install

Clone the repository and install the CLI:

```bash
git clone https://github.com/your-name/proxyctl.git
cd proxyctl
make install
```

By default this installs to `/usr/local/bin/proxyctl`. To install somewhere else:

```bash
make install PREFIX="$HOME/.local"
```

You can also run it directly without installing:

```bash
./src/proxyctl help
```

## Quick Start

Run setup:

```bash
proxyctl setup
```

Turn the proxy on:

```bash
proxyctl on
```

If Clash Verge manages your system proxy and routing rules, choose backend `none` during `proxyctl setup`. In that mode `proxyctl on` only starts the local SSH SOCKS endpoint, and Clash can use it as an upstream proxy.

Make terminal programs in the current shell use the proxy:

```bash
eval "$(proxyctl env)"
```

Check state:

```bash
proxyctl status
```

Turn the proxy off:

```bash
proxyctl off
```

Unset proxy variables in the current shell:

```bash
eval "$(proxyctl unenv)"
```

## SSH Destination

The SSH destination is anything accepted by `ssh`, for example:

```text
my-vps
user@example.com
203.0.113.10
```

If you use a short name such as `my-vps`, define it in `~/.ssh/config` or make sure it resolves through DNS.

## Development

Run tests:

```bash
make test
```

Run lint and tests:

```bash
make check
```

The test suite uses stub commands and temporary home directories. It does not change the host system proxy settings or open real SSH connections.

This project was written collaboratively by humans and AI.
