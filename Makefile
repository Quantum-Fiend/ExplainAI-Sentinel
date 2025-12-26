.PHONY: build up down restart logs status

build:
	@echo "🏗 Building all services..."
	docker-compose -f deployment/docker-compose.yml build

up:
	@echo "🚀 Starting all services..."
	docker-compose -f deployment/docker-compose.yml up -d

down:
	@echo "🛑 Stopping all services..."
	docker-compose -f deployment/docker-compose.yml down

restart:
	@echo "🔄 Restarting all services..."
	docker-compose -f deployment/docker-compose.yml restart

logs:
	@echo "📑 Viewing logs..."
	docker-compose -f deployment/docker-compose.yml logs -f

status:
	@echo "📊 Service status..."
	docker-compose -f deployment/docker-compose.yml ps

lint:
	@echo "🧹 Linting polyglot codebase..."
	pre-commit run --all-files

deploy-helm:
	@echo "☸️ Deploying to Kubernetes via Helm..."
	helm upgrade --install sentinel ./deployment/helm --namespace explainai-sentinel --create-namespace
