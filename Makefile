.PHONY: install start test flatpak update-deps

install:
	poetry lock
	poetry install

start:
	python3 lgtv_remote.py

test:
	poetry run pytest tests/ -v

flatpak:
	flatpak install --noninteractive flathub org.gnome.Platform//49 org.gnome.Sdk//49 || true
	flatpak-builder --user --install --force-clean build-dir io.github.wh1le.CouchCommander.yml
