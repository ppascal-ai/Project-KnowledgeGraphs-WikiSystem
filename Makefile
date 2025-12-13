.PHONY: up down logs seed test

up:
	docker-compose up --build -d

down:
	docker-compose down

logs:
	docker-compose logs -f api

seed:
	docker-compose exec api python scripts/seed_data.py

test:
	docker-compose exec api pytest