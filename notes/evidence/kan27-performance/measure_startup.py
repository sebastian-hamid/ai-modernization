#!/usr/bin/env python3
"""Time a fresh KAN-27 disposable candidate stack through protected-API readiness."""
import argparse, json, os, subprocess, time, urllib.error, urllib.request
from pathlib import Path


def run(args, cwd, env):
    return subprocess.run(args, cwd=cwd, env=env, check=True, text=True,
                          stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def health(container):
    return subprocess.run(["docker","inspect","-f","{{.State.Health.Status}}",container],
                          capture_output=True,text=True,check=True).stdout.strip()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--secret-dir",required=True)
    parser.add_argument("--project",required=True,help="new unique Compose project name")
    parser.add_argument("--output",required=True)
    parser.add_argument("--port",type=int,default=8082)
    args=parser.parse_args()
    repo=Path(__file__).resolve().parents[3]
    compose_dir=repo/"infrastructure/database"
    env=os.environ.copy()
    env.update({"KAN22_SECRET_DIR":str(Path(args.secret_dir).resolve()),
                "KAN18_APP_IMAGE":os.environ.get("KAN18_APP_IMAGE","ai-modernization-kan27-performance:candidate")})
    base=["docker","compose","-p",args.project,"-f",str(compose_dir/"compose.yaml")]
    existing=subprocess.run(["docker","ps","-aq","--filter","label=com.docker.compose.project="+args.project],
                            capture_output=True,text=True,check=True).stdout.strip()
    labelled_volumes=subprocess.run(["docker","volume","ls","-q","--filter","label=com.docker.compose.project="+args.project],
                                   capture_output=True,text=True,check=True).stdout.strip()
    labelled_networks=subprocess.run(["docker","network","ls","-q","--filter","label=com.docker.compose.project="+args.project],
                                    capture_output=True,text=True,check=True).stdout.strip()
    exact_resources=[]
    for kind,name in (("volume",args.project+"_postgres_data"),
                      ("network",args.project+"_database"),
                      ("network",args.project+"_candidate-host-access")):
        result=subprocess.run(["docker",kind,"inspect",name],capture_output=True,text=True)
        if result.returncode==0: exact_resources.append(kind+":"+name)
    if existing or labelled_volumes or labelled_networks or exact_resources:
        parser.error("Compose project containers, volumes or networks already exist; choose a new project name")
    overall=time.monotonic()
    phase=time.monotonic(); run(base+["up","-d","postgres"],compose_dir,env)
    postgres=f"{args.project}-postgres-1"
    deadline=time.monotonic()+90
    while time.monotonic()<deadline and health(postgres)!="healthy": time.sleep(.5)
    if health(postgres)!="healthy": parser.error("PostgreSQL did not become healthy within 90 seconds")
    postgres_seconds=round(time.monotonic()-phase,3)
    phase=time.monotonic(); run(base+["--profile","migrate","run","--rm","migrate"],compose_dir,env)
    migration_seconds=round(time.monotonic()-phase,3)
    phase=time.monotonic(); run(base+["--profile","candidate-app","up","-d","candidate-app"],compose_dir,env)
    compose_up_command_seconds=round(time.monotonic()-phase,3)
    app_started=time.monotonic(); url=f"http://127.0.0.1:{args.port}/cargo-tracker/rest/cargo"; status=None
    deadline=time.monotonic()+90
    while time.monotonic()<deadline:
        try:
            with urllib.request.urlopen(url,timeout=2) as response: status=response.status
        except urllib.error.HTTPError as error: status=error.code
        except Exception: status=None
        if status==401: break
        time.sleep(.25)
    if status!=401: parser.error(f"Candidate protected API readiness failed: HTTP {status}")
    app_seconds=round(time.monotonic()-app_started,3)
    result={"project":args.project,"readiness_url":url,"readiness_http":status,
            "postgres_to_healthy_seconds":postgres_seconds,
            "migration_command_seconds":migration_seconds,
            "candidate_app_to_ready_seconds":app_seconds,"candidate_compose_up_command_seconds":compose_up_command_seconds,
            "full_stack_to_ready_seconds":round(time.monotonic()-overall,3),
            "includes_image_build":False,"volume_is_new":True}
    Path(args.output).write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))

if __name__=="__main__": main()
