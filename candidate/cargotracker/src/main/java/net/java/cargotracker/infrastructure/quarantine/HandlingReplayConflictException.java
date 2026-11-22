package net.java.cargotracker.infrastructure.quarantine;

/** Signals that a quarantine entry is not eligible for another manual replay. */
@jakarta.ejb.ApplicationException(rollback = true)
public class HandlingReplayConflictException extends RuntimeException {
    public HandlingReplayConflictException(String message) { super(message); }
}
