# KAN-15 current mobile handling wrong-CSRF evidence

This evidence adds a negative security check for current mobile handling submissions. For both Operator and Administrator, Chromium filled the live form with a routed cargo, LOAD, a valid location, a future completion time, and an available voyage. It submitted the captured form and ViewState after changing only the CSRF token to an invalid value.

Both requests returned HTTP 403. The response contained no cargo/location/acceptance payload, and before/after observations of database tables, JMS queues, and business invocations were unchanged. The full native fixture passed 777 checks; Chromium passed 922 checks; both task-owned containers and the private network were removed.

The live current-capability gate reports 470 PASS, 44 RETIRED, and 32 BLOCKED retirement cases (exit 2). This supplemental proof does not promote any retirement rows. Full results and their SHA-256 digests are recorded in validation.json.

The two failed diagnostic attempts are documented there so the final passing run remains auditable.
