all: run

init_dev:
	@python3 -m venv .venv
	@. .venv/bin/activate; pip install --upgrade pip -r requirements.txt -r requirements-dev.txt

## Runs application. Builds, creates, starts, and attaches to containers for a service. | Common
run:
	@mkdir -p data && chmod 777 data
	@docker compose up -d --build

## Stops application. Stops running container without removing them.
stop:
	@docker compose stop

## Removes stopped service containers.
clean:
	@docker compose down --remove-orphans

## Starts container for debug
debug:
	@docker compose -f docker-compose.debug.yml up -d --build

stopdebug:
	@docker compose -f docker-compose.debug.yml down --remove-orphans