#!/usr/bin/env python3
"""Create private disposable credentials required by the KAN-27 Compose fixture."""
import argparse, hashlib, json, os, secrets
from pathlib import Path

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("directory",help="new private directory outside the Git checkout")
    args=parser.parse_args()
    root=Path(args.directory).resolve()
    root.mkdir(parents=True,mode=0o700,exist_ok=False)
    values={name:secrets.token_urlsafe(32) for name in ("bootstrap_password","app_password","migrator_password")}
    passwords={name:secrets.token_urlsafe(32) for name in ("reader","operator","admin")}
    contents={**{name:value+"\n" for name,value in values.items()},
      "application-users.properties":"#$REALM_NAME=ApplicationRealm$\n"+"".join(
        name+"="+hashlib.md5((name+":ApplicationRealm:"+password).encode()).hexdigest()+"\n"
        for name,password in passwords.items()),
      "application-roles.properties":"reader=Reader\noperator=Operator\nadmin=Administrator\n",
      "application-passwords.json":json.dumps(passwords)}
    for name,content in contents.items():
        path=root/name
        path.write_text(content)
        path.chmod(0o444)
    root.chmod(0o700)
    print("Created private KAN-27 disposable credentials at",root)
if __name__=="__main__": main()