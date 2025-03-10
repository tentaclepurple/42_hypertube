.PHONY: up all down exec execf env clean

all: up

up:
	docker compose up -d

upf:
	docker compose up

down:
	docker compose down

exec:
	docker exec -it backend bash -c "cd app && bash"

execf:
	docker exec -it frontend bash


env:
	@if [ -f .env ]; then \
		echo ".env file already exists. Skipping .env creation."; \
	else \
		read -p "Enter your key: " key; \
		echo "Downloading .env file..."; \
		curl -L "https://www.$$key.com/scl/fi/xq4kwbk1z5rpwy1etgr8l/env?rlkey=fl913obdcaddlo9m06ced0ng9&dl=1" -o .env; \
		echo ".env file has been downloaded."; \
	fi

logs:
	docker logs backend

logsf:
	docker logs  -f frontend

clean: down
	yes | docker system prune -a