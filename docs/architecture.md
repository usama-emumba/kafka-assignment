# CDC Data Lake Pipeline - Architecture

## Quick Access

| Service | URL | Credentials |
|---------|-----|-------------|
| pgAdmin | http://localhost:5050 | admin@admin.com / admin |
| Grafana | http://localhost:3000 | admin / admin |
| MinIO Console | http://localhost:9001 | admin / password123 |


---

## Overview

Real-time CDC pipeline replicating PostgreSQL to MinIO with sub-10 second latency.

**Features:** Debezium CDC, Kafka streaming, PII exclusion, Parquet storage (70% compression), date partitioning, Prometheus monitoring

**Stack:** PostgreSQL, Debezium , Kafka , Schema Registry, MinIO, Grafana

---

## Architecture


**Flow:** DB changes → Debezium captures → Kafka topics → Schema validation → Transform (remove PII) → Parquet conversion → MinIO storage with date partitions

---

## Components

**PostgreSQL:** Logical replication enabled, 4 tables (customers, products, orders, order_items)

**Debezium:** PostgreSQL connector, captures changes in real-time, publishes to Kafka

**Kafka:** Central messaging system, stores streams of records in categories (topics)

**Schema Registry:** Manages Avro schemas for Kafka topics, ensures compatibility

**MinIO:** S3-compatible object storage, stores data lake files in Parquet format

**Grafana/Prometheus:** Monitoring and alerting for pipeline health and performance

---

## Monitoring

**Prometheus scrapes:** kafka-exporter:9308, postgres-exporter:9187, minio:9000

**Grafana panels:** Connector health, topic message count, consumer lag

**Key metrics:** `kafka_topic_partition_current_offset`, `kafka_consumergroup_lag`, `up{job="kafka-connect"}`

---

## Storage Format

### Parquet Format Benefits

| Feature | Benefit |
|---------|---------|
| Columnar Storage | Read only required columns (reduces I/O by 90%) |
| Compression | 70% smaller than JSON (Snappy algorithm) |
| Schema Evolution | Schema embedded in file metadata |
| Predicate Pushdown | Filter data before reading |
| Type Safety | Strong typing prevents data corruption |
| Cloud-Native | Optimized for S3/MinIO object storage |

### Partition Strategy

**Date-Based Partitioning:**
```
s3://my-data-lake/
  topics/
    customers/
      year=2024/
        month=01/
          day=01/
            customers+0+0000000000.snappy.parquet
            customers+0+0000000100.snappy.parquet
          day=02/
            customers+0+0000000200.snappy.parquet
        month=02/
          day=01/
            customers+0+0000000300.snappy.parquet
```

**Query Optimization:**
```sql
-- Only scans day=15 partition (fast)
SELECT * FROM customers WHERE year=2024 AND month=01 AND day=15;

-- Scans entire table (slow)
SELECT * FROM customers WHERE created_at > '2024-01-15';
```

### File Rotation Strategy

**Rotation Triggers:**
1. **Size-based:** `flush.size=5` records
2. **Time-based:** `rotate.interval.ms=60000` (60 seconds)
3. **Shutdown:** Connector graceful stop

**Example Rotation:**
```
10:00:00 - Insert 3 records → Wait
10:00:30 - Insert 2 records → Total 5 → File rotated (flush.size reached)
10:01:00 - Insert 1 record → Wait
10:02:00 - Timer expires → File rotated (rotate.interval.ms reached)
```

### Compression Comparison

| Format | Size | Compression Ratio |
|--------|------|-------------------|
| JSON (uncompressed) | 100 MB | 1x |
| JSON (gzip) | 25 MB | 4x |
| Parquet (Snappy) | 15 MB | 6.7x |
| Parquet (gzip) | 12 MB | 8.3x (slower write) |

**Snappy chosen for:**
- Fast compression/decompression
- Good compression ratio
- CPU-efficient for real-time pipelines
