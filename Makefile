.PHONY: doctor test verify install sync snapshots

doctor:
	./scripts/doctor

test:
	python3 -m unittest discover -s tests -v
	@for script in scripts/* home/.local/bin/*; do \
		[ -f "$$script" ] || continue; \
		head -n 1 "$$script" | grep -Eq '(bash|zsh|sh)' || continue; \
		bash -n "$$script" 2>/dev/null || zsh -n "$$script"; \
	done

verify:
	./scripts/verify --source

install:
	./scripts/install --apply

sync:
	./scripts/sync-all

snapshots:
	./scripts/export-runtime-snapshots
