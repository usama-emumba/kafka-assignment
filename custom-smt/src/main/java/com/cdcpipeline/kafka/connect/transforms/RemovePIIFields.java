package com.cdcpipeline.kafka.connect.transforms;

import org.apache.kafka.common.config.ConfigDef;
import org.apache.kafka.connect.connector.ConnectRecord;
import org.apache.kafka.connect.data.Field;
import org.apache.kafka.connect.data.Schema;
import org.apache.kafka.connect.data.SchemaBuilder;
import org.apache.kafka.connect.data.Struct;
import org.apache.kafka.connect.transforms.Transformation;
import org.apache.kafka.connect.transforms.util.SimpleConfig;

import java.util.*;

/**
 * Custom SMT to remove PII fields from Kafka Connect records.
 * 
 * This transform:
 * 1. Takes a list of field names to remove
 * 2. Creates a new schema WITHOUT those fields
 * 3. Creates a new record WITHOUT those fields
 * 
 * Configuration:
 *   fields.to.remove: Comma-separated list (e.g., "email,phone")
 */
public class RemovePIIFields<R extends ConnectRecord<R>> implements Transformation<R> {

    private static final String FIELDS_TO_REMOVE_CONFIG = "fields.to.remove";
    
    private Set<String> fieldsToRemove;

    @Override
    public ConfigDef config() {
        return new ConfigDef()
            .define(
                FIELDS_TO_REMOVE_CONFIG,
                ConfigDef.Type.LIST,
                ConfigDef.NO_DEFAULT_VALUE,
                ConfigDef.Importance.HIGH,
                "Comma-separated list of field names to remove (e.g., email,phone)"
            );
    }

    @Override
    public void configure(Map<String, ?> configs) {
        final SimpleConfig config = new SimpleConfig(config(), configs);
        
        // Get the list of fields to remove from configuration
        List<String> fields = config.getList(FIELDS_TO_REMOVE_CONFIG);
        this.fieldsToRemove = new HashSet<>(fields);
        
        System.out.println("RemovePIIFields SMT configured to remove fields: " + fieldsToRemove);
    }

    @Override
    public R apply(R record) {
        if (record.value() == null || !(record.value() instanceof Struct)) {
            return record;
        }

        System.out.println("CUSTOM SMT PROCESSING RECORD!");
        
        final Struct originalValue = (Struct) record.value();
        final Schema originalSchema = originalValue.schema();
        
        System.out.println("Original fields: " + originalSchema.fields().stream()
            .map(Field::name)
            .collect(java.util.stream.Collectors.joining(", ")));
        
        final Schema newSchema = buildSchemaWithoutPIIFields(originalSchema);
        final Struct newValue = buildValueWithoutPIIFields(originalValue, newSchema);
        
        System.out.println("New fields after PII removal: " + newSchema.fields().stream()
            .map(Field::name)
            .collect(java.util.stream.Collectors.joining(", ")));

        return record.newRecord(
            record.topic(),
            record.kafkaPartition(),
            record.keySchema(),
            record.key(),
            newSchema,
            newValue,
            record.timestamp()
        );
    }

    /**
     * Build a new schema that excludes PII fields
     */
    private Schema buildSchemaWithoutPIIFields(Schema originalSchema) {
        final SchemaBuilder builder = SchemaBuilder.struct();
        
        // Copy schema metadata
        if (originalSchema.name() != null) {
            builder.name(originalSchema.name());
        }
        if (originalSchema.doc() != null) {
            builder.doc(originalSchema.doc());
        }
        
        // Add all fields EXCEPT the ones we want to remove
        for (Field field : originalSchema.fields()) {
            if (!fieldsToRemove.contains(field.name())) {
                // Keep this field
                builder.field(field.name(), field.schema());
            } else {
                System.out.println("Removing field from schema: " + field.name());
            }
        }
        
        return builder.build();
    }

    /**
     * Build a new record value that excludes PII fields
     */
    private Struct buildValueWithoutPIIFields(Struct originalValue, Schema newSchema) {
        final Struct newValue = new Struct(newSchema);
        
        // Copy all field values EXCEPT the ones we want to remove
        for (Field field : originalValue.schema().fields()) {
            if (!fieldsToRemove.contains(field.name())) {
                // Copy this field's value
                newValue.put(field.name(), originalValue.get(field));
            } else {
                System.out.println("Removing field data: " + field.name());
            }
        }
        
        return newValue;
    }

    @Override
    public void close() {
        // Cleanup if needed
        System.out.println("RemovePIIFields SMT closed");
    }
}
