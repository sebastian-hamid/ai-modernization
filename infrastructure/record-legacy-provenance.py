#!/usr/bin/env python3
# Record origins and hashes of recovered historical artifacts.
from pathlib import Path
import hashlib
import argparse
import json
import sys
import xml.etree.ElementTree as ET

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

parser=argparse.ArgumentParser()
parser.add_argument("root",type=Path)
parser.add_argument("workspace",type=Path)
parser.add_argument("evidence",type=Path)
parser.add_argument("--expected-tests",type=int,default=24)
parser.add_argument("--test-overlay-root",type=Path)
args=parser.parse_args()
root, workspace, evidence = args.root,args.workspace,args.evidence
require(args.expected_tests>0,"Expected a positive test count")
cache = root / ".work/m2"
items = []
for path in sorted((cache / "org/eclipse/persistence").rglob("*")):
    if path.suffix not in {".jar", ".pom"}:
        continue
    relative = path.relative_to(cache).as_posix()
    remote = path.parent / "_remote.repositories"
    origins = remote.read_text() if remote.exists() else ""
    repository_ids = [
        line.split(">", 1)[1].split("=", 1)[0]
        for line in origins.splitlines() if line.startswith(path.name + ">")
    ]
    # Maven Resolver may append a context hash to the configured repository ID.
    if any(repo == "eclipselink-https" or repo.startswith("eclipselink-https-") for repo in repository_ids):
        origin = "https://download.eclipse.org/rt/eclipselink/maven.repo/"
    elif any(repo in {"central", "central-https"} or repo.startswith("central-https-") for repo in repository_ids):
        origin = "https://repo.maven.apache.org/maven2/"
    else:
        raise RuntimeError(f"No recognized download origin for {relative}: {repository_ids}")
    items.append({"artifact": relative, "origin": origin + relative,
                  "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                  "recovery": "downloaded; version unchanged"})
for relative, url, commit in [
    ("org/primefaces/maven-jsf-plugin/1.3.0/maven-jsf-plugin-1.3.0.jar",
     "https://github.com/primefaces/maven-jsf-plugin", "60774367fba1287c2a838ac78799b32c563c0acf"),
    ("org/primefaces/themes/ui-lightness/1.0.10/ui-lightness-1.0.10.jar",
     "https://github.com/primefaces/themes", "db6195c272cd7b2567c60b4ed786e44bbecf5db0"),
]:
    path = cache / relative
    items.append({"artifact": relative, "source_repository": url, "source_commit": commit,
                  "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                  "recovery": "rebuilt from unmodified official release tag; published-binary equality unverified"})
war = workspace / "source/target/cargo-tracker.war"
suites = [ET.parse(p).getroot() for p in sorted((evidence / "surefire-reports").glob("TEST-*.xml"))]
counts = {key: sum(int(s.get(key, "0")) for s in suites)
          for key in ("tests", "failures", "errors", "skipped")}
require(counts["tests"] == args.expected_tests and counts["failures"] == counts["errors"] == counts["skipped"] == 0, counts)
result = {"application_repository": "https://github.com/javaee/cargotracker",
          "application_commit": "57fc7b32d2597e43b5e0d454e707e0146de5258a",
          "container": "maven@sha256:b9fac8295f9d342af5d815888dca1334b12833a84c870c260b88f31285c1ef3d",
          "war_path": str(war), "war_sha256": hashlib.sha256(war.read_bytes()).hexdigest(),
          "domain_test_results": counts, "known_empty_test": "ItineraryTest.testNextExpectedEvent",
          "artifacts": items}
if args.test_overlay_root:
    result["test_overlay_sha256"]={
        path.relative_to(args.test_overlay_root).as_posix():hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(args.test_overlay_root.rglob("*.java"))
    }
    require(bool(result["test_overlay_sha256"]),"Expected external characterization test sources")
(evidence / "dependency-provenance.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(counts))
