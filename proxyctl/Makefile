.PHONY: test lint check install uninstall

PREFIX ?= /usr/local
BINDIR ?= $(PREFIX)/bin

test:
	bash tests/test_proxyctl.sh

lint:
	@if command -v shellcheck >/dev/null 2>&1; then \
		shellcheck src/proxyctl tests/test_proxyctl.sh; \
	else \
		echo "shellcheck is not installed; skipping local lint."; \
		echo "GitHub Actions installs shellcheck and runs this lint in CI."; \
	fi

check: lint test

install:
	install -d "$(DESTDIR)$(BINDIR)"
	install -m 0755 src/proxyctl "$(DESTDIR)$(BINDIR)/proxyctl"

uninstall:
	rm -f "$(DESTDIR)$(BINDIR)/proxyctl"
