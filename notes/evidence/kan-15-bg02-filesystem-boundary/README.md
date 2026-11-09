# KAN-15 BG-02 trusted filesystem staging boundary

Date: 9 November 2026

## Scope and result

The disposable WildFly fixture exercised the Administrator-triggered batch importer using approved fixture administration tooling to stage files. The server's incoming, archive, and failed directories were verified as mode 700 and owned by the WildFly OS identity (UID 1000). An unrelated untrusted OS identity (UID 65534) was denied listing, reading, and writing each directory; marker files were absent after the probes.

The valid staged input was consumed, persisted as a handling event, and archived under the generated in-root name. A malformed input was consumed into failed output and was not archived or processed as a business event. The native fixture passed 728 checks and Chromium passed 841 checks. Cleanup removed the owned runtime and private files with no errors.

BG-02-MACHINE passes in the fresh gate. The full gate has 449 current PASS / 21 BLOCKED, 324 historical PASS / 178 BLOCKED, and 76 retirement BLOCKED. Gate exit 2 reflects remaining unrelated blocked inventory. The input fingerprint is `5f855b30bfca64555a04421e9ed7569b6732844db8c54357bb087aa6bb7b3113`.

See [sanitized validation summary](validation.json) and [full sanitized current gate](current-capability-gate.json).

## Limits

This proves filesystem permissions and job behavior only in the disposable fixture, for the modeled approved root administration tooling and UID 65534. It does not attest production host ACLs, operating-system identity management, or deployment controls. The batch-worker's application identity remains distinct from the filesystem's server process UID.
