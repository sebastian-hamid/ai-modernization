#!/usr/bin/env python3
# Refresh the exact non-secret input set without replacing the Docker bind mount.
from pathlib import Path
import hashlib
import json
import shutil

root=Path(__file__).resolve().parents[1]
managed=root/".work/jenkins-ci"
snapshot=managed/"source"
if snapshot.is_symlink() or snapshot.resolve()!=managed.resolve()/"source":
    raise RuntimeError("Snapshot must be the managed source directory")
snapshot.mkdir(parents=True,exist_ok=True)
files={"Jenkinsfile":root/"Jenkinsfile","VERSION":root/"VERSION"}
for folder in ["ci","infrastructure","tests"]:
    for path in (root/folder).rglob("*"):
        if path.is_symlink():
            raise RuntimeError(f"Snapshot inputs must not be symlinks: {path}")
        if "__pycache__" in path.parts or path.suffix==".pyc":
            continue
        if path.is_file():
            files[path.relative_to(root).as_posix()]=path
# Reject symlinks before writing or removing any managed snapshot content.
existing=list(snapshot.rglob("*"))
if any(p.is_symlink() for p in existing):
    raise RuntimeError("Managed snapshot contains a symlink")
manifest={relative:hashlib.sha256(path.read_bytes()).hexdigest() for relative,path in sorted(files.items())}
# Remove stale files individually; never traverse out of this managed directory.
for path in existing:
    if path.is_file() and path.relative_to(snapshot).as_posix() not in files:
        path.unlink()
for relative,path in files.items():
    target=snapshot/relative
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(path,target)
encoded=json.dumps(manifest,indent=2)+"\n"
(snapshot/"source-snapshot.json").write_text(encoded)
evidence=root/"notes/evidence"
evidence.mkdir(parents=True,exist_ok=True)
(evidence/"jenkins-source-snapshot.json").write_text(encoded)
print("Exact pipeline input snapshot updated:",snapshot)
print("Start the idle Jenkins job to use it. Jenkinsfile definition edits require updating the job definition separately.")
