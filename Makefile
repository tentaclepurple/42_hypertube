.PHONY: standalone front back down clean logs help re

standalone:
	@echo "Starting STANDALONE mode..."
	docker compose -f docker-compose.standalone.yml --env-file .env.standalone up -d

front:
	@echo "=== FRONTEND MODULAR MODE ==="
	@LOCAL_IP=$$(ip route get 1 | awk '{print $$7; exit}' 2>/dev/null || \
	             ipconfig getifaddr en0 2>/dev/null || \
	             hostname -I | awk '{print $$1}' 2>/dev/null || \
	             echo "127.0.0.1"); \
	echo "Detected frontend IP: $$LOCAL_IP"; \
	read -p "Enter BACKEND IP (e.g., 192.168.1.100): " backend_ip; \
	if [ -z "$$backend_ip" ]; then \
		echo "ERROR: Backend IP is required"; \
		exit 1; \
	fi; \
	echo "NEXT_PUBLIC_URL=http://$$backend_ip:8000" > .env.front.tmp; \
	echo "BACKEND_INTERNAL_URL=http://$$backend_ip:8000" >> .env.front.tmp; \
	grep -v "^NEXT_PUBLIC_URL=" .env.front | grep -v "^BACKEND_INTERNAL_URL=" >> .env.front.tmp; \
	echo "Starting FRONTEND (frontend: $$LOCAL_IP, connecting to backend at $$backend_ip)..."; \
	NEXT_PUBLIC_URL=http://$$backend_ip:8000 BACKEND_INTERNAL_URL=http://$$backend_ip:8000 docker compose -f docker-compose.front.yml --env-file .env.front.tmp up -d; \
	rm -f .env.front.tmp

back:
	@echo "=== BACKEND MODULAR MODE ==="
	@LOCAL_IP=$$(ip route get 1 | awk '{print $$7; exit}' 2>/dev/null || \
	             ipconfig getifaddr en0 2>/dev/null || \
	             hostname -I | awk '{print $$1}' 2>/dev/null || \
	             echo "127.0.0.1"); \
	echo "Detected backend IP: $$LOCAL_IP"; \
	read -p "Enter FRONTEND IP (e.g., 192.168.1.101): " frontend_ip; \
	if [ -z "$$frontend_ip" ]; then \
		echo "ERROR: Frontend IP is required"; \
		exit 1; \
	fi; \
	echo "BACKEND_URL=http://$$LOCAL_IP:8000" > .env.back.tmp; \
	echo "FRONTEND_URL=http://$$frontend_ip:3000" >> .env.back.tmp; \
	grep -v "^BACKEND_URL=" .env.back | grep -v "^FRONTEND_URL=" >> .env.back.tmp; \
	echo "Starting BACKEND + services (backend: $$LOCAL_IP, frontend: $$frontend_ip)..."; \
	BACKEND_URL=http://$$LOCAL_IP:8000 FRONTEND_URL=http://$$frontend_ip:3000 docker compose -f docker-compose.back.yml --env-file .env.back.tmp up -d; \
	rm -f .env.back.tmp

down:
	@echo "Stopping all services..."
	docker compose -f docker-compose.standalone.yml down 2>/dev/null || true
	docker compose -f docker-compose.front.yml down 2>/dev/null || true
	docker compose -f docker-compose.back.yml down 2>/dev/null || true

re-standalone: down standalone

re-front: down front

re-back: down back

logs:
	docker logs -f backend

logsf:
	docker logs -f frontend

logst:
	docker logs -f torrent_service

logsk:
	docker logs -f kafka

logsz:
	docker logs -f zookeeper

exec:
	docker exec -it backend bash

execf:
	docker exec -it frontend bash

clean: down
	yes | docker system prune -a
	rm -f .env.front.tmp .env.back.tmp

help:
	@echo "Available commands:"
	@echo ""
	@echo "  make standalone      - Run all services (localhost)"
	@echo "  make front           - Run only frontend (auto-detects frontend IP, asks for backend IP)"
	@echo "  make back            - Run backend + services (auto-detects backend IP, asks for frontend IP)"
	@echo "  make down            - Stop all services"
	@echo ""
	@echo "  make re-standalone   - Restart standalone"
	@echo "  make re-front        - Restart frontend"
	@echo "  make re-back         - Restart backend"
	@echo ""
	@echo "  make logs            - Backend logs"
	@echo "  make logsf           - Frontend logs"
	@echo "  make logst           - Torrent service logs"
	@echo "  make logsk           - Kafka logs"
	@echo "  make logsz           - Zookeeper logs"
	@echo ""
	@echo "  make exec            - Bash into backend"
	@echo "  make execf           - Bash into frontend"
	@echo ""
	@echo "  make clean           - Clean Docker system"