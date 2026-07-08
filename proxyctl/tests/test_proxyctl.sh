#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN="${ROOT_DIR}/src/proxyctl"

TEST_TMP=""

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

assert_contains() {
  local haystack="$1"
  local needle="$2"
  [[ "$haystack" == *"$needle"* ]] || fail "expected output to contain: $needle"
}

assert_file_contains() {
  local file="$1"
  local needle="$2"
  [[ -f "$file" ]] || fail "missing file: $file"
  grep -Fq "$needle" "$file" || fail "expected $file to contain: $needle"
}

setup_tmp() {
  TEST_TMP="$(mktemp -d)"
  mkdir -p "$TEST_TMP/bin" "$TEST_TMP/home"
}

cleanup_tmp() {
  [[ -n "$TEST_TMP" && -d "$TEST_TMP" ]] && rm -rf "$TEST_TMP"
  return 0
}

trap cleanup_tmp EXIT

write_stub_ssh_success() {
  cat >"$TEST_TMP/bin/ssh" <<'EOF'
#!/usr/bin/env bash
if [[ "$1" == "-G" ]]; then
  exit 0
fi
if [[ "$*" == *" -O check "* ]]; then
  exit 1
fi
if [[ "$*" == *" -O exit "* ]]; then
  exit 0
fi
exit 0
EOF
  chmod +x "$TEST_TMP/bin/ssh"
}

write_stub_ssh_fail() {
  cat >"$TEST_TMP/bin/ssh" <<'EOF'
#!/usr/bin/env bash
if [[ "$1" == "-G" ]]; then
  exit 0
fi
printf 'ssh: Could not resolve hostname example.invalid\n' >&2
exit 255
EOF
  chmod +x "$TEST_TMP/bin/ssh"
}

write_stub_networksetup() {
  cat >"$TEST_TMP/bin/networksetup" <<'EOF'
#!/usr/bin/env bash
log="${PROXYCTL_STUB_LOG:?}"
printf 'networksetup %s\n' "$*" >>"$log"
case "$1" in
  -listallnetworkservices)
    printf 'An asterisk (*) denotes that a network service is disabled.\nWi-Fi\nEthernet\n'
    ;;
  -getinfo)
    printf 'IP address: 192.0.2.10\n'
    ;;
  -getsocksfirewallproxy)
    printf 'Enabled: Yes\nServer: 127.0.0.1\nPort: 7899\nAuthenticated Proxy Enabled: 0\n'
    ;;
esac
EOF
  chmod +x "$TEST_TMP/bin/networksetup"
}

write_stub_gsettings() {
  cat >"$TEST_TMP/bin/gsettings" <<'EOF'
#!/usr/bin/env bash
log="${PROXYCTL_STUB_LOG:?}"
printf 'gsettings %s\n' "$*" >>"$log"
if [[ "$1" == "get" && "$3" == "mode" ]]; then
  printf "'manual'\n"
elif [[ "$1" == "get" && "$4" == "host" ]]; then
  printf "'127.0.0.1'\n"
elif [[ "$1" == "get" && "$4" == "port" ]]; then
  printf "7899\n"
fi
EOF
  chmod +x "$TEST_TMP/bin/gsettings"
}

write_stub_lsof_busy() {
  cat >"$TEST_TMP/bin/lsof" <<'EOF'
#!/usr/bin/env bash
if [[ "$*" == *"127.0.0.1:7901"* ]]; then
  printf 'COMMAND PID USER FD TYPE DEVICE SIZE/OFF NODE NAME\n'
  printf 'ssh 123 user 3u IPv4 0 0t0 TCP 127.0.0.1:7901 (LISTEN)\n'
  exit 0
fi
exit 1
EOF
  chmod +x "$TEST_TMP/bin/lsof"
}

run_proxyctl() {
  HOME="$TEST_TMP/home" \
  XDG_CONFIG_HOME="$TEST_TMP/home/.config" \
  XDG_STATE_HOME="$TEST_TMP/home/.local/state" \
  PATH="$TEST_TMP/bin:$PATH" \
  PROXYCTL_STUB_LOG="$TEST_TMP/stub.log" \
  "$BIN" "$@"
}

test_help() {
  setup_tmp
  local output
  output="$(run_proxyctl help)"
  assert_contains "$output" "Usage:"
  assert_contains "$output" "Linux desktop proxy is currently supported for GNOME"
  cleanup_tmp
  TEST_TMP=""
}

test_macos_setup_and_env() {
  setup_tmp
  write_stub_ssh_success
  write_stub_networksetup

  printf 'user@example.com\n\n\nmacos\nWi-Fi\n' | PROXYCTL_TEST_OS=macos PROXYCTL_SKIP_PORT_CHECK=1 run_proxyctl setup >/tmp/proxyctl-test.out

  local config="$TEST_TMP/home/.config/proxyctl/config"
  assert_file_contains "$config" "SSH_DESTINATION=user@example.com"
  assert_file_contains "$config" "SYSTEM_BACKEND=macos"
  assert_file_contains "$config" "SYSTEM_TARGET=Wi-Fi"

  local env_output
  env_output="$(run_proxyctl env)"
  assert_contains "$env_output" "ALL_PROXY=socks5h://127.0.0.1:7899"
  cleanup_tmp
  TEST_TMP=""
}

test_linux_gnome_setup_and_on() {
  setup_tmp
  write_stub_ssh_success
  write_stub_gsettings

  printf 'user@example.com\n\n\ngnome\n' | PROXYCTL_TEST_OS=linux PROXYCTL_SKIP_PORT_CHECK=1 run_proxyctl setup >/tmp/proxyctl-test.out

  local config="$TEST_TMP/home/.config/proxyctl/config"
  assert_file_contains "$config" "SYSTEM_BACKEND=gnome"

  PROXYCTL_TEST_OS=linux PROXYCTL_TEST_TUNNEL_ALIVE=1 run_proxyctl on >/tmp/proxyctl-test.out
  assert_file_contains "$TEST_TMP/stub.log" "gsettings set org.gnome.system.proxy.socks host 127.0.0.1"
  assert_file_contains "$TEST_TMP/stub.log" "gsettings set org.gnome.system.proxy.socks port 7899"
  assert_file_contains "$TEST_TMP/stub.log" "gsettings set org.gnome.system.proxy mode manual"
  cleanup_tmp
  TEST_TMP=""
}

test_macos_on_calls_networksetup() {
  setup_tmp
  write_stub_ssh_success
  write_stub_networksetup

  printf 'user@example.com\n\n\nmacos\nWi-Fi\n' | PROXYCTL_TEST_OS=macos PROXYCTL_SKIP_PORT_CHECK=1 run_proxyctl setup >/tmp/proxyctl-test.out
  PROXYCTL_TEST_OS=macos PROXYCTL_TEST_TUNNEL_ALIVE=1 run_proxyctl on >/tmp/proxyctl-test.out

  assert_file_contains "$TEST_TMP/stub.log" "networksetup -setsocksfirewallproxy Wi-Fi 127.0.0.1 7899"
  assert_file_contains "$TEST_TMP/stub.log" "networksetup -setsocksfirewallproxystate Wi-Fi on"
  cleanup_tmp
  TEST_TMP=""
}

test_macos_none_backend_skips_networksetup() {
  setup_tmp
  write_stub_ssh_success
  write_stub_networksetup

  printf 'user@example.com\n\n\nnone\n' | PROXYCTL_TEST_OS=macos PROXYCTL_SKIP_PORT_CHECK=1 run_proxyctl setup >/tmp/proxyctl-test.out
  PROXYCTL_TEST_OS=macos PROXYCTL_TEST_TUNNEL_ALIVE=1 run_proxyctl on >/tmp/proxyctl-test.out

  local output
  output="$(cat /tmp/proxyctl-test.out)"
  assert_contains "$output" "No system proxy backend is configured."
  if [[ -f "$TEST_TMP/stub.log" ]]; then
    ! grep -Fq -- "-setsocksfirewallproxy" "$TEST_TMP/stub.log" || fail "none backend should not call networksetup proxy setters"
  fi
  cleanup_tmp
  TEST_TMP=""
}

test_port_busy_error() {
  setup_tmp
  write_stub_ssh_success
  write_stub_lsof_busy

  mkdir -p "$TEST_TMP/home/.config/proxyctl"
  cat >"$TEST_TMP/home/.config/proxyctl/config" <<'EOF'
SSH_DESTINATION=user@example.com
SOCKS_HOST=127.0.0.1
SOCKS_PORT=7901
SYSTEM_BACKEND=none
SYSTEM_TARGET=
EOF

  set +e
  local output
  output="$(PROXYCTL_TEST_OS=linux run_proxyctl on 2>&1)"
  local code=$?
  set -e
  [[ "$code" -ne 0 ]] || fail "expected port-busy test to fail"
  assert_contains "$output" "The local SOCKS port is already in use"
  assert_contains "$output" "Process currently listening"
  cleanup_tmp
  TEST_TMP=""
}

test_ssh_failure_error() {
  setup_tmp
  write_stub_ssh_fail

  mkdir -p "$TEST_TMP/home/.config/proxyctl"
  cat >"$TEST_TMP/home/.config/proxyctl/config" <<'EOF'
SSH_DESTINATION=example.invalid
SOCKS_HOST=127.0.0.1
SOCKS_PORT=7902
SYSTEM_BACKEND=none
SYSTEM_TARGET=
EOF

  set +e
  local output
  output="$(PROXYCTL_TEST_OS=linux PROXYCTL_SKIP_PORT_CHECK=1 run_proxyctl on 2>&1)"
  local code=$?
  set -e
  [[ "$code" -ne 0 ]] || fail "expected SSH failure test to fail"
  assert_contains "$output" "Could not start the SSH SOCKS tunnel"
  assert_contains "$output" "ssh -N -D 127.0.0.1:7902 example.invalid"
  cleanup_tmp
  TEST_TMP=""
}

test_legacy_config_compatibility() {
  setup_tmp
  write_stub_networksetup

  mkdir -p "$TEST_TMP/home/.config/proxyctl"
  cat >"$TEST_TMP/home/.config/proxyctl/config" <<'EOF'
SSH_HOST=legacy-host
SOCKS_HOST=127.0.0.1
SOCKS_PORT=7899
NETWORK_SERVICE=Wi-Fi
EOF

  local output
  output="$(PROXYCTL_TEST_OS=macos PROXYCTL_SKIP_PORT_CHECK=1 run_proxyctl status)"
  assert_contains "$output" "SSH destination:  legacy-host"
  assert_contains "$output" "System backend:   macos"
  assert_contains "$output" "System target:    Wi-Fi"
  cleanup_tmp
  TEST_TMP=""
}

test_help
test_macos_setup_and_env
test_linux_gnome_setup_and_on
test_macos_on_calls_networksetup
test_macos_none_backend_skips_networksetup
test_port_busy_error
test_ssh_failure_error
test_legacy_config_compatibility

printf 'All tests passed.\n'
