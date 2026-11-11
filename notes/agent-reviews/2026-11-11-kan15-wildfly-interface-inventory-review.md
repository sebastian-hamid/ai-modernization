# KAN-15 BG-06 WildFly interface inventory review

- Task: Document the candidate application and WildFly interface inventory relevant to startup seeding and schema migration.
- Source revision: `c2bf55c` (`Verify remote JNDI and JMS authentication`).
- Author: `/root`.
- Separate reviewer: `/root/review_kan18_postgres_prerun`.
- Review date: 2026-11-11.
- Scope: `docs/candidate/wildfly-interface-inventory.md`; link and scope note in `docs/candidate/bg06-startup-and-migration-boundary.md`.
- Final SHA-256: `2f1a8499601bbc5a6d1a456d638650c4a899817309461bad6d499d1d25168c17` (boundary); `3bafb3b1649315a9ff0d37f91cb0b991f32e167d22c19aa9e0d93eebbf655041` (inventory).
- Review checks: compared interface paths, EJB/CDI/JNDI references, JMS destinations/consumers and RunAs identities against candidate source/config; checked broker dead-letter routing against `notification-disposition.cli`; checked the pinned WildFly listener config against the KAN-18 raw/compact receipts; confirmed the TCP-only and BG-06 scope limitations.
- Finding and response: the first review identified that broker dead-letter routing populates the rejected-registration queue; corrected the document to distinguish that route from Java producers and include the onward DLQ after three failed deliveries. Added the HandlingAttemptProducer RunAs identity; reviewer confirmed its annotation, mapped principal and broker role.
- Verification: `git diff --check` passed. Reviewer did not edit, run tests, or launch a runtime.
- Verdict: approved; no remaining material findings.
- Limitations: this is a source/config inventory supplemented by existing KAN-18 runtime receipts. It does not pass a BG-06 case; all five BG-06 cases remain BLOCKED pending a trusted gate adapter and actor/effects evidence.
