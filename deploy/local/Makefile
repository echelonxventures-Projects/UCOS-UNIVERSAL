# Local development stack (deploy/local/compose.yaml).
COMPOSE := docker compose -f compose.yaml
.PHONY: up down logs ps reset
up:     ## start everything and wait until healthy
	$(COMPOSE) up -d --wait
down:   ## stop
	$(COMPOSE) down
reset:  ## stop and delete data (the schema is re-applied on next start)
	$(COMPOSE) down -v
logs:
	$(COMPOSE) logs -f
ps:
	$(COMPOSE) ps
