package net.java.cargotracker.infrastructure.quarantine;

/** Signals that a durable intake message cannot yet fit in the approved quarantine. */
@jakarta.ejb.ApplicationException(rollback = true, inherited = true)
public final class QuarantineCapacityFullException extends RuntimeException {
    private static final long serialVersionUID = 1L;
    private final String requestId;
    private final String messageKey;
    private final long usedBytes;
    private final long messageBytes;
    private final long capacityBytes;

    public QuarantineCapacityFullException(String requestId, String messageKey, long usedBytes, long messageBytes, long capacityBytes) {
        super("Handling quarantine is at its configured capacity");
        this.requestId = requestId;
        this.messageKey = messageKey;
        this.usedBytes = usedBytes;
        this.messageBytes = messageBytes;
        this.capacityBytes = capacityBytes;
    }
    public String requestId() { return requestId; }
    public String messageKey() { return messageKey; }
    public long usedBytes() { return usedBytes; }
    public long messageBytes() { return messageBytes; }
    public long capacityBytes() { return capacityBytes; }
}