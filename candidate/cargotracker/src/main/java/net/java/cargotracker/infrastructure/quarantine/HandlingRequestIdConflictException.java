package net.java.cargotracker.infrastructure.quarantine;

/** Signals reuse of a stable handling request ID with a different event payload. */
@jakarta.ejb.ApplicationException(rollback = true)
public class HandlingRequestIdConflictException extends RuntimeException {
    public HandlingRequestIdConflictException(String message) { super(message); }
}
