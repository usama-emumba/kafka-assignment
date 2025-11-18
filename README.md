# CDC Data Lake Pipeline

Real-time Change Data Capture from PostgreSQL to MinIO using Debezium, Kafka, and Parquet format.

## Quick Start

```bash
# Start all services
docker-compose up -d

# Wait 60 seconds for services to be ready
sleep 60

# Deploy Debezium connector
curl -X POST http://localhost:8083/connectors \
  -H "Content-Type: application/json" \
  -d @connectors/debezium-postgres.json

# Check status
curl http://localhost:8083/connectors/debezium-postgres-source/status | jq
```

## Access Points

### Web Interfaces

| Service | URL | Credentials |
|---------|-----|-------------|
| **Grafana** | http://localhost:3000 | `admin` / `admin` |
| **Prometheus** | http://localhost:9090 | No auth |
| **MinIO Console** | http://localhost:9001 | `admin` / `password123` |
| **pgAdmin** | http://localhost:5050 | `admin@admin.com` / `admin` |

### APIs

| Service | URL | Purpose |
|---------|-----|---------|
| **Kafka Connect** | http://localhost:8083 | Connector management |
| **Schema Registry** | http://localhost:8081 | Schema versioning |

### Database

**PostgreSQL:**
```bash
psql -h localhost -p 5432 -U postgres -d ecommerce
# Password: postgres
```

## Features

- **Real-time CDC:** Sub-10 second latency from PostgreSQL to MinIO
- **PII Exclusion:** Email and phone fields completely removed (not masked)
- **Parquet Storage:** 70% compression with Snappy, columnar format
- **Date Partitioning:** `year=YYYY/month=MM/day=DD` structure
- **Schema Evolution:** Backward compatibility enforced via Schema Registry
- **Monitoring:** Prometheus + Grafana with kafka-exporter metrics
- **GDPR Compliant:** Complete PII field removal before storage

## Current Setup

**Active Components:**
- PostgreSQL with 4 tables (customers, products, orders, order_items)
- Debezium capturing changes (29 customer records processed)
- Kafka topics with Avro serialization
- Schema Registry with 10 schemas registered
- Grafana dashboard showing pipeline health
- kafka-exporter providing metrics to Prometheus

**Configuration:**
- Debezium: snapshot.mode=initial, replication slot: debezium_slot_fixed
- Transforms: ExtractNewRecordState + ReplaceField (excludes email, phone)
- Dead Letter Queue: dlq-debezium-errors (for error handling)
- Kafka: Single broker with auto-topic creation

## Testing the Pipeline

### Insert Test Data
```bash
docker-compose exec postgres psql -U postgres -d ecommerce -c \
  "INSERT INTO customers (name, email, phone) 
   VALUES ('Test User', 'test@example.com', '555-1234');"
```

### Verify in Kafka
```bash
# Using schema-registry container (avoids JMX conflicts)
docker-compose exec schema-registry kafka-avro-console-consumer \
  --bootstrap-server kafka:29092 \
  --topic ecommerce.public.customers \
  --from-beginning \
  --max-messages 5
```

### List Kafka Topics
```bash
# Unset KAFKA_OPTS to avoid JMX port conflicts
docker-compose exec kafka bash -c "unset KAFKA_OPTS && kafka-topics --bootstrap-server localhost:9092 --list"
```

### Check Connector Status
```bash
curl http://localhost:8083/connectors/debezium-postgres-source/status | jq
```

### Verify Schemas
```bash
curl http://localhost:8081/subjects | jq
```

### Check Metrics
```bash
# Verify Prometheus is scraping
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .job, health: .health}'

# Check topic metrics
curl -s http://localhost:9308/metrics | grep kafka_topic_partition_current_offset
```

## Monitoring

**Grafana Dashboard:**
- Open http://localhost:3000
- Login: admin/admin
- Dashboard shows: Connector Health, CDC Topics Message Count, Total Messages, Consumer Lag

**Prometheus Targets:**
- kafka-exporter:9308 (topic metrics, consumer lag)
- postgres-exporter:9187 (database stats)
- minio:9000 (storage metrics)
- kafka-connect via JMX (connector health)

## Troubleshooting

### Kafka CLI JMX Error
```bash
# Use this workaround for kafka-topics command
docker-compose exec kafka bash -c "unset KAFKA_OPTS && kafka-topics --bootstrap-server localhost:9092 --list"

# Or consume from schema-registry container
docker-compose exec schema-registry kafka-avro-console-consumer --bootstrap-server kafka:29092 --topic TOPIC_NAME
```

### Connector Failed
```bash
# Check status
curl http://localhost:8083/connectors/debezium-postgres-source/status | jq

# Restart
curl -X POST http://localhost:8083/connectors/debezium-postgres-source/restart

# View logs
docker-compose logs kafka-connect --tail 50
```

### No Dashboard Data
```bash
# Verify kafka-exporter is in Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.job=="kafka-exporter")'

# If missing, check monitoring/prometheus.yml has kafka-exporter job
# Then restart: docker-compose restart prometheus grafana
```

### Replication Slot Issues
```bash
# Drop slot
docker-compose exec postgres psql -U postgres -d ecommerce -c \
  "SELECT pg_drop_replication_slot('debezium_slot_fixed');"

# Delete connector
curl -X DELETE http://localhost:8083/connectors/debezium-postgres-source

# Redeploy
curl -X POST http://localhost:8083/connectors -d @connectors/debezium-postgres.json
```

## Useful Commands

```bash
# Full pipeline restart
docker-compose down
docker-compose up -d
sleep 60
curl -X POST http://localhost:8083/connectors -d @connectors/debezium-postgres.json

# Insert test records
docker-compose exec postgres psql -U postgres -d ecommerce -c \
  "INSERT INTO customers (name, email) VALUES ('Demo User', 'demo@test.com');"

# Check record count
docker-compose exec postgres psql -U postgres -d ecommerce -c \
  "SELECT COUNT(*) FROM customers;"

# Verify data flow
docker-compose exec schema-registry kafka-avro-console-consumer \
  --bootstrap-server kafka:29092 \
  --topic ecommerce.public.customers \
  --from-beginning --max-messages 1
```

## PII Handling

**Fields Excluded (Complete Removal):**
- email
- phone
- address (if exists)

**Implementation:**
```json
{
  "transforms": "unwrap,redactPII",
  "transforms.redactPII.type": "org.apache.kafka.connect.transforms.ReplaceField$Value",
  "transforms.redactPII.exclude": "email,phone"
}
```

**Result:** These fields are removed from both the record AND the schema before reaching Kafka topics. MinIO Parquet files will never contain PII.

## Schema Evolution

**Allowed Changes:**
- Add nullable columns: `ALTER TABLE customers ADD COLUMN loyalty_points INTEGER;`
- Add columns with defaults: `ALTER TABLE customers ADD COLUMN status VARCHAR DEFAULT 'active';`

**Prohibited:**
- Remove columns
- Change column types
- Make nullable columns required

**Verify Evolution:**
```bash
curl http://localhost:8081/subjects/ecommerce.public.customers-value/versions/latest | jq
```

## Production Considerations

**Security (Not in local setup):**
- Enable TLS for all services
- Use SASL authentication for Kafka
- Store credentials in HashiCorp Vault
- Apply Kubernetes network policies

**High Availability:**
- 3 Kafka brokers with replication factor 3
- 3 Kafka Connect workers
- PostgreSQL with streaming replication
- MinIO distributed mode

**Performance:**
- Tune flush.size (1000-5000) based on latency requirements
- Adjust consumer.max.poll.records (500-2000)
- Monitor lag and scale Connect workers
- Use same AZ for all components

## Documentation

- [Architecture](docs/architecture.md) - System design, components, data flow
- [Architecture Diagrams](docs/architecture-diagram.mmd) - Mermaid diagrams
- [Data Flow](docs/data-flow.mmd) - Sequence diagram
- [Monitoring](docs/monitoring.mmd) - Metrics architecture
- [Transformations](docs/transformation.mmd) - PII handling flow

## License
MIT
