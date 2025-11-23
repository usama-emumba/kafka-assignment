#!/bin/bash
# filepath: /Users/usamaamjad/VSCode_Python/cdc-data-lake-pipeline/custom-smt/build.sh

set -e

echo "========================================="
echo "Building Custom PII Field Remover SMT"
echo "========================================="

# Create target directory
mkdir -p target

echo ""
echo "Step 1: Building JAR using Docker (this will take 2-3 minutes)..."
docker build -t pii-field-remover-builder .

echo ""
echo "Step 2: Extracting JAR from Docker image..."
docker run --rm -v $(pwd)/target:/target pii-field-remover-builder

# Verify JAR was created
if [ -f "target/pii-field-remover-1.0.0-jar-with-dependencies.jar" ]; then
    echo ""
    echo "✓ JAR built successfully!"
    ls -lh target/pii-field-remover-1.0.0-jar-with-dependencies.jar
else
    echo ""
    echo "✗ JAR build failed!"
    exit 1
fi

echo ""
echo "Step 3: Copying JAR to Kafka Connect container..."
docker cp target/pii-field-remover-1.0.0-jar-with-dependencies.jar kafka-connect:/usr/share/java/

echo ""
echo "Step 4: Restarting Kafka Connect to load new SMT..."
docker-compose restart kafka-connect

echo ""
echo "========================================="
echo "✓ Build Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Wait 60 seconds for Kafka Connect to restart"
echo "2. Delete old connector:"
echo "   curl -X DELETE http://localhost:8083/connectors/debezium-postgres-source"
echo ""
echo "3. Deploy connector with custom SMT:"
echo "   curl -X POST http://localhost:8083/connectors \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d @../connectors/debezium-postgres-custom-smt.json"
echo ""
echo "4. Check status:"
echo "   curl http://localhost:8083/connectors/debezium-postgres-source/status | jq"
echo ""
echo "========================================="