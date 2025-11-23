# Custom PII Field Remover SMT

## What This Does

This custom Single Message Transform (SMT) **completely removes** specified fields from Kafka records.

**Flow:**

1. The connector reads the data from the source (e.g., a database).
2. The SMT processes each record, removing any fields that match the configured PII criteria.
3. The transformed record is then sent to the sink (e.g., a data lake or another database).

## Prerequisites

- Java 11 or higher
- Maven 3.6+
- Docker and docker-compose

## Build Steps

1. Install Maven (if not already installed):
```bash
# macOS
brew install maven

# Or download from https://maven.apache.org/download.cgi
```

2. Build the custom SMT:
```bash
cd custom-smt
mvn clean package
```

3. Copy JAR to Kafka Connect:
```bash
docker cp target/pii-redaction-smt-1.0.0-jar-with-dependencies.jar kafka-connect:/usr/share/java/
```

4. Restart Kafka Connect:
```bash
docker-compose restart kafka-connect
sleep 30
```

5. Deploy connector with custom SMT:
```bash
curl -X POST http://localhost:8083/connectors \
  -H "Content-Type: application/json" \
  -d @../connectors/debezium-postgres-custom-smt.json
```

## Redaction Strategies

| Strategy | Description | Example |
|----------|-------------|---------|
| HASH | SHA-256 hash | `john@example.com` → `5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8` |
| MASK | Mask with asterisks | `555-1234` → `***-1234` |
| LAST4 | Keep last 4 chars | `555-1234` → `1234` |
| REMOVE | Remove field | Field doesn't exist in output |
| TOKENIZE | Random UUID | `john@example.com` → `a3f5e1b2-4d6c-8e9f-1234-567890abcdef` |

## Configuration Examples

See `connectors/examples/` for different strategy configurations.

## Testing

Run the test script:
```bash
./test-smt.sh
```

Check that email is hashed/masked according to your strategy.
