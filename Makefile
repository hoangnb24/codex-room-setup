.PHONY: doctor test test-container verify install sync snapshots

doctor:
	./scripts/doctor

test:
	python3 -m unittest discover -s tests -v
	python3 -m py_compile scripts/install-room
	@for script in scripts/* home/.local/bin/*; do \
		[ -f "$$script" ] || continue; \
		head -n 1 "$$script" | grep -Eq '(bash|zsh|sh)' || continue; \
		bash -n "$$script" 2>/dev/null || zsh -n "$$script"; \
	done

test-container:
	./tests/container/run

verify:
	./scripts/verify --source

install:
	./install --apply

sync:
	./scripts/sync-all

snapshots:
	./scripts/export-runtime-snapshots
