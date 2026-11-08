package net.java.cargotracker.interfaces.handling.file;

import java.io.Serializable;

public record BatchImportResult(String runId, long executionId, String initiatedBy) implements Serializable {}
