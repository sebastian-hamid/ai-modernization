#!/usr/bin/env python3
# Native Java 8 steps for the isolated Jenkins agent; no Docker daemon access.
from pathlib import Path
import json
import hashlib
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

def require(condition, message):
    if not condition:
        raise RuntimeError(message)


ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/".work/ci"
RESULTS=ROOT/"ci-results"
EVIDENCE=ROOT/"notes/evidence/recovered-baseline-ci"
SETTINGS=ROOT/"infrastructure/legacy-maven-settings.xml"
CACHE=ROOT/".work/m2"
APP="57fc7b32d2597e43b5e0d454e707e0146de5258a"
def run(command, log, cwd=ROOT, timeout=900):
    log.parent.mkdir(parents=True,exist_ok=True)
    print("Running:", " ".join(map(str,command)),flush=True)
    with log.open("w") as output:
        result=subprocess.run(list(map(str,command)),cwd=cwd,stdout=output,stderr=subprocess.STDOUT,timeout=timeout)
    if result.returncode:
        print(log.read_text()[-14000:],flush=True)
        raise RuntimeError(f"Command exited {result.returncode}; see {log}")
def mvn(project, log, *args):
    run(["mvn","-B","-ntp","-s",SETTINGS,f"-Dmaven.repo.local={CACHE}",f"-Dorg.apache.maven.user-settings={SETTINGS}",*args],log,WORK/project)
def source(name,url,commit):
    dest=WORK/name
    run(["git","clone","--quiet","--no-checkout",url,dest],RESULTS/"sources"/(name+".log"))
    run(["git","checkout","--quiet",commit],RESULTS/"sources"/(name+"-checkout.log"),dest)
    require(subprocess.check_output(["git","rev-parse","HEAD"],cwd=dest,text=True).strip()==commit, 'Required setup invariant failed')
def overlay(name):
    original=(WORK/"source/pom.xml").read_text()
    require("<skipTests>true</skipTests>" in original, 'Required setup invariant failed')
    (WORK/"source"/name).write_text(original.replace("<skipTests>true</skipTests>","<skipTests>false</skipTests>"))
def reports(destination,pattern):
    destination.mkdir(parents=True,exist_ok=True)
    for report in (WORK/"source/target/surefire-reports").glob(pattern):
        shutil.copy2(report,destination/report.name)
def assert_reports(directory,expected):
    suites=[ET.parse(p).getroot() for p in directory.glob("TEST-*.xml")]
    counts={k:sum(int(s.get(k,"0")) for s in suites) for k in ("tests","failures","errors","skipped")}
    require(counts==dict(tests=expected,failures=0,errors=0,skipped=0), counts)
    print("Verified test results:",counts,flush=True)
def sources():
    manifest_path=ROOT/"source-snapshot.json"
    manifest=json.loads(manifest_path.read_text())
    for relative,expected in manifest.items():
        path=ROOT/relative
        require(path.is_file() and not path.is_symlink(), f"Invalid snapshot input: {relative}")
        require(hashlib.sha256(path.read_bytes()).hexdigest()==expected, f"Snapshot input changed: {relative}")
    WORK.mkdir(parents=True,exist_ok=True)
    CACHE.mkdir(parents=True,exist_ok=True)
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    RESULTS.mkdir(parents=True,exist_ok=True)
    shutil.copy2(manifest_path, RESULTS/"source-snapshot.json")
    shutil.copy2(ROOT/"VERSION", RESULTS/"VERSION")
    run(["java","-version"],RESULTS/"java8.txt")
    run(["/opt/java21/bin/java","-version"],RESULTS/"agent-java21.txt")
    run(["mvn","-version"],EVIDENCE/"toolchain.txt")
    source("source","https://github.com/javaee/cargotracker.git",APP)
    source("plugin","https://github.com/primefaces/maven-jsf-plugin.git","60774367fba1287c2a838ac78799b32c563c0acf")
    source("themes","https://github.com/primefaces/themes.git","db6195c272cd7b2567c60b4ed786e44bbecf5db0")
def package():
    mvn("plugin",EVIDENCE/"jsf-plugin-build.log","-DskipTests","install")
    mvn("themes",EVIDENCE/"theme-build.log","-DskipTests","-pl","ui-lightness","-am","install")
    mvn("source",EVIDENCE/"package.log","package")
    shutil.copy2(WORK/"source/target/cargo-tracker.war",RESULTS/"cargo-tracker.war")
def domain():
    # Add test-only sources to the exported checkout after the untouched WAR build.
    shutil.copytree(ROOT/"tests/java",WORK/"source/src/test/java",dirs_exist_ok=True)
    overlay("domain-tests-pom.xml")
    try:
        mvn("source",EVIDENCE/"domain-tests.log","-f","domain-tests-pom.xml","-Dtest=CargoTest,ItineraryTest,RouteSpecificationTest,HandlingEventTest,HandlingHistoryTest,HandlingFactoryCharacterizationTest","test")
    finally:
        reports(RESULTS/"domain","TEST-*.xml")
    assert_reports(RESULTS/"domain",34)
    reports(EVIDENCE/"surefire-reports","TEST-*.xml")
    run(["python3",ROOT/"infrastructure/record-legacy-provenance.py",ROOT,WORK,EVIDENCE,"--expected-tests","34","--test-overlay-root",ROOT/"tests/java"],RESULTS/"provenance.log")
def runtime():
    run(["python3",ROOT/"infrastructure/prepare-legacy-runtime.py"],RESULTS/"runtime/prepare.log")
    runtime_root=ROOT/".work/glassfish-runtime"
    gf=runtime_root/"unpacked/glassfish4"
    shutil.copy2(runtime_root/"patches/bean-validator.jar",gf/"glassfish/modules/bean-validator.jar")
    for bindir in [gf/"bin",gf/"glassfish/bin"]:
        for path in bindir.iterdir():
            if path.is_file():path.chmod(path.stat().st_mode | 0o111)
    admin=gf/"bin/asadmin"
    try:
        run([admin,"start-domain","domain1"],RESULTS/"runtime/start.log",timeout=120)
        run([admin,"deploy","--name","cargo-tracker","--contextroot","cargo-tracker",runtime_root/"cargo-tracker.war"],RESULTS/"runtime/deploy.log",timeout=120)
        overlay("integration-tests-pom.xml")
        try:
            mvn("source",RESULTS/"integration/booking.log","-f","integration-tests-pom.xml","-Dtest=BookingServiceTest","test")
        finally:
            reports(RESULTS/"integration","TEST-*BookingServiceTest.xml")
        assert_reports(RESULTS/"integration",4)
        run(["python3",ROOT/"infrastructure/smoke-legacy-runtime.py","--base-url","http://127.0.0.1:8080/cargo-tracker/","--exercise-handling"],RESULTS/"runtime/workflow-smoke.log",timeout=120)
        run(["python3",ROOT/"tests/runtime/handling_workflow.py","--base-url","http://127.0.0.1:8080/cargo-tracker/",
             "--server-log",gf/"glassfish/domains/domain1/logs/server.log",
             "--report-dir",RESULTS/"handling","--allow-mutation"],
             RESULTS/"runtime/handling-characterization.log",timeout=180)
        assert_reports(RESULTS/"handling",15)
        run(["python3",ROOT/"tests/runtime/entrypoint_contracts.py","--base-url","http://127.0.0.1:8080/cargo-tracker/",
             "--report-dir",RESULTS/"entrypoints","--allow-mutation"],
             RESULTS/"runtime/entrypoint-contracts.log",timeout=180)
        assert_reports(RESULTS/"entrypoints",81)
    finally:
        try:
            run([admin,"stop-domain","domain1"],RESULTS/"runtime/stop.log",timeout=60)
        finally:
            log=gf/"glassfish/domains/domain1/logs/server.log"
            if log.exists():shutil.copy2(log,RESULTS/"runtime/server.log")
if __name__=="__main__":
    {"sources":sources,"package":package,"domain":domain,"runtime":runtime}[sys.argv[1]]()
