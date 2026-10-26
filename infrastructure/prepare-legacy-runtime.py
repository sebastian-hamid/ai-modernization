#!/usr/bin/env python3
# Recover the historical runtime and apply the precise HK2-277 metadata correction.
from pathlib import Path
import hashlib
import json
import re
import shutil
import urllib.request
import zipfile

def require(condition, message):
    if not condition:
        raise RuntimeError(message)


root=Path(__file__).resolve().parents[1]
work=root/".work/glassfish-runtime"
work.mkdir(parents=True,exist_ok=True)
url="https://download.oracle.com/glassfish/4.1/release/glassfish-4.1.zip"
expected="3edc5fc72b8be241a53eae83c22f274479d70e15bdfba7ba2302da5260f23e9d"
archive=work/"glassfish-4.1.zip"
if not archive.exists():
    partial=archive.with_suffix(".zip.part")
    with urllib.request.urlopen(url,timeout=120) as response,partial.open("wb") as output:
        shutil.copyfileobj(response,output)
    require(hashlib.sha256(partial.read_bytes()).hexdigest()==expected, "Downloaded GlassFish archive hash changed")
    partial.replace(archive)
require(hashlib.sha256(archive.read_bytes()).hexdigest()==expected, "GlassFish archive hash changed")
unpacked=work/"unpacked"
with zipfile.ZipFile(archive) as z:
    for name in z.namelist():
        require((unpacked/name).resolve().is_relative_to(unpacked.resolve()), "Unsafe archive path")
    z.extractall(unpacked)
source=unpacked/"glassfish4/glassfish/modules/bean-validator.jar"
corrected=work/"patches/bean-validator.jar"
corrected.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(source) as zin,zipfile.ZipFile(corrected,"w") as zout:
    require(not any(n.upper().endswith((".SF",".RSA",".DSA")) for n in zin.namelist()), 'Required setup invariant failed')
    for info in zin.infolist():
        data=zin.read(info.filename)
        if info.filename=="META-INF/MANIFEST.MF":
            text=re.sub(r"\r?\n ","",data.decode())
            old=',org.hibernate.validator.internal.cdi.interceptor;version="5.0.0.Final",org.hibernate.validator.internal.cdi;version="5.0.0.Final"'
            require(text.count(old)==1, "Unexpected validator manifest")
            text=text.replace(old,"")
            lines=[]
            for line in text.splitlines():
                while len(line.encode())>70:
                    lines.append(line[:70])
                    line=" "+line[70:]
                lines.append(line)
            data=("\r\n".join(lines)+"\r\n").encode()
        zout.writestr(info,data)
with zipfile.ZipFile(source) as before,zipfile.ZipFile(corrected) as after:
    require(before.namelist()==after.namelist(), 'Required setup invariant failed')
    require(all(before.read(n)==after.read(n) for n in before.namelist() if n!="META-INF/MANIFEST.MF"), "Patch changed more than metadata")
manifests=sorted((root/"notes/evidence").glob("recovered-baseline-*/dependency-provenance.json"))
require(manifests, "Run infrastructure/recover-legacy-baseline.sh first")
manifest=json.loads(manifests[-1].read_text())
war=Path(manifest["war_path"])
require(hashlib.sha256(war.read_bytes()).hexdigest()==manifest["war_sha256"], "WAR differs from verified baseline")
shutil.copy2(war,work/"cargo-tracker.war")
for name in ["Dockerfile","start.sh"]:
    shutil.copy2(root/"infrastructure/glassfish"/name,work/name)
proof={"glassfish_url":url,"glassfish_zip_sha256":expected,
       "container_base":"maven@sha256:b9fac8295f9d342af5d815888dca1334b12833a84c870c260b88f31285c1ef3d",
       "runtime_correction":"HK2-277: remove two false CDI package exports from bean-validator.jar manifest; all other entry bytes verified unchanged",
       "issue":"https://github.com/javaee/hk2/issues/277",
       "validator_original_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
       "validator_corrected_sha256":hashlib.sha256(corrected.read_bytes()).hexdigest(),
       "war_sha256":manifest["war_sha256"],
       "build_evidence":str(manifests[-1].relative_to(root))}
(root/"notes/evidence/glassfish-runtime-provenance.json").write_text(json.dumps(proof,indent=2)+"\n")
print("Prepared verified runtime context:",work)
