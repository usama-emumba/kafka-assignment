.PHONY: help start stop logs status deploy-connectors verify clean

help:
	@echo "📚 CDC Pipeline Makefile Commands:"
	@echo "  make start              - Start all services with Docker Compose"
	@echo "  make stop               - Stop all services"
	@echo "  make logs               - Follow logs from all services"
	@echo "  make status             - Check status of all services"
	@echo "  make deploy-connectors  - Deploy Kafka Connect connectors"
	@echo "  make verify             - Verify pipeline is working"
	@echo "  make clean              - Stop and remove all volumes"
	@echo "  make k8s-deploy         - Deploy to Kubernetes"

start:
	@echo "🚀 Starting CDC Pipeline..."
	docker-compose up -d
	@echo "⏳ Waiting for services to be healthy..."
	@sleep 90
	@chmod +x scripts/deploy-connectors.sh
	@./scripts/deploy-connectors.sh

stop:
	@echo "🛑 Stopping services..."
	docker-compose down

logs:
	docker-compose logs -f

status:
	@echo "=== Debezium Status ==="
	@curl -s http://localhost:8083/connectors/debezium-postgres-source/status | jq '.connector.state, .tasks[0].state'
	@echo ""
	@echo "=== S3 Sink Status ==="
	@curl -s http://localhost:8083/connectors/s3-sink-connector/status | jq '.connector.state, .tasks[0].state'

status-detailed:
	@curl -s http://localhost:8083/connectors/debezium-postgres-source/status | jq
	@echo ""
	@curl -s http://localhost:8083/connectors/s3-sink-connector/status | jq

deploy-connectors:
	@chmod +x scripts/deploy-connectors.sh
	@./scripts/deploy-connectors.sh

verify:
	@chmod +x scripts/verify-pipeline.sh
	@./scripts/verify-pipeline.sh

clean:
	@echo "🧹 Cleaning up..."
	docker-compose down -v
	@echo "All volumes removed"

k8s-deploy:
	@echo "Deploying to Kubernetes..."
	cd terraform && terraform init && terraform apply -auto-approve
	@chmod +x k8s/deploy-all.sh
	@./k8s/deploy-all.sh

compact-customers:
	. .venv/bin/activate && python scripts/compact_customers.py

reset-full:
	./reset-and-load-all-data.sh

read-customers:
	. .venv/bin/activate && python read_parquet.py ecommerce.public.customers
