#!/usr/bin/env python3
"""Real WildFly authentication/session tests; test fixture is not Cargo Tracker."""
from pathlib import Path
import hashlib,http.cookiejar,json,re,secrets,shutil,subprocess,time,urllib.request,urllib.error,urllib.parse
ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT/".work/kan15"
NAME="ai-modernization-kan15"
IMAGE="ai-modernization-kan15:security-fixture"
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None
def command(*args):return subprocess.check_output(args,stderr=subprocess.STDOUT,text=True).strip()
def finalize(container,paths,report):
    errors=[]
    if container:
        try:(WORK/"server.log").write_text(command("docker","logs",container))
        except Exception as error:errors.append("logs:"+type(error).__name__)
        try:
            command("docker","rm","-f",container)
            report["owned_container_removed"]=True
        except Exception as error:
            report["owned_container_removed"]=False
            errors.append("remove:"+type(error).__name__)
    for path in paths:
        try:
            if path.exists():path.unlink()
        except Exception as error:errors.append("private-cleanup:"+type(error).__name__)
    report["private_files_removed"]=all(not path.exists() for path in paths)
    report["cleanup_errors"]=errors
    if errors:report["status"]="FAIL"
    report["count"]=len(report["checks"])
    (WORK/"results.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"status":report["status"],"checks":report["count"],"private_files_removed":report["private_files_removed"]}))
    return not errors

def main():
    WORK.mkdir(parents=True,exist_ok=True)
    private=WORK/"secrets";private.mkdir(exist_ok=True,mode=0o700);private.chmod(0o700)
    users=private/"application-users.properties";roles=private/"application-roles.properties"
    if users.exists() or roles.exists():raise RuntimeError("Private files exist; inspect before reuse")
    if subprocess.run(["docker","inspect",NAME],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:raise RuntimeError("Task container already exists")
    credentials={who:secrets.token_urlsafe(28) for who in ["reader","operator","admin"]}
    container=None;checks=[]
    report={"task":"KAN-15","scope":"Reusable security component integration fixture; not migrated Cargo Tracker","checks":checks,"status":"FAIL"}
    def check(name,condition):
        checks.append({"name":name,"passed":bool(condition)})
        if not condition:raise AssertionError(name)
    def client():
        jar=http.cookiejar.CookieJar()
        return jar,urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar),NoRedirect())
    base=None
    def request(opener,path,data=None,token=None,method=None):
        headers={}
        if token:headers["X-CSRF-Token"]=token
        if isinstance(data,dict):data=urllib.parse.urlencode(data).encode();headers["Content-Type"]="application/x-www-form-urlencoded"
        req=urllib.request.Request(base+path,data=data,headers=headers,method=method)
        try:res=opener.open(req,timeout=10)
        except urllib.error.HTTPError as error:res=error
        with res:return res.status,res.read().decode(),res.headers
    def login(who):
        jar,opener=client()
        code,body,_=request(opener,"login")
        match=re.search("name='csrf' value='([^']+)'",body);check("Login form with token: "+who,code==200 and match is not None)
        old=next(c.value for c in jar if c.name=="JSESSIONID")
        code,_,_=request(opener,"login",{"username":who,"password":credentials[who],"csrf":match[1]})
        check("Container login succeeds: "+who,code==303)
        new=next(c.value for c in jar if c.name=="JSESSIONID")
        check("Session ID rotates: "+who,old!=new)
        code,body,_=request(opener,"session")
        role={"reader":"Reader","operator":"Operator","admin":"Administrator"}[who]
        check("Server principal and role: "+who,code==200 and body.startswith(who+"|"+role+"|"))
        return jar,opener,body.split("|")[2]
    try:
        users.write_text("#$REALM_NAME=ApplicationRealm$\n"+"".join(who+"="+hashlib.md5((who+":ApplicationRealm:"+pw).encode()).hexdigest()+"\n" for who,pw in credentials.items()))
        roles.write_text("reader=Reader\noperator=Operator\nadmin=Administrator\n")
        users.chmod(0o600);roles.chmod(0o600)
        context=WORK/"context";context.mkdir(exist_ok=True)
        for relative in ["candidate/security","tests/security-runtime"]:
            target=context/relative
            shutil.copytree(ROOT/relative,target,dirs_exist_ok=True,ignore=shutil.ignore_patterns("target","__pycache__"))
        with (WORK/"image-build.log").open("w") as log:
            proc=subprocess.run(["docker","build","--progress=plain","-f",str(context/"tests/security-runtime/Dockerfile"),"-t",IMAGE,str(context)],stdout=log,stderr=subprocess.STDOUT)
        check("Pinned runtime fixture builds",proc.returncode==0)
        report["image_id"]=command("docker","image","inspect","--format","{{.Id}}",IMAGE)
        container=command("docker","run","-d","--name",NAME,"--label","ai-modernization.task=KAN-15","--init","-p","127.0.0.1::8080","--mount",f"type=bind,src={private},dst=/run/kan15,readonly",IMAGE)
        port=int(command("docker","port",container,"8080/tcp").rsplit(":",1)[1])
        base=f"http://127.0.0.1:{port}/security-fixture/"
        deadline=time.monotonic()+150
        anonymous=client()[1]
        while time.monotonic()<deadline:
            try:
                if request(anonymous,"public")[0]==200:break
            except OSError:pass
            time.sleep(1)
        else:raise RuntimeError("Fixture deployment not ready")
        check("Anonymous read denied",request(anonymous,"read")[0]==401)
        code,_,headers=request(anonymous,"page.xhtml")
        check("Protected page navigates to login",code==303 and headers["Location"]=="/security-fixture/login")
        check("Unknown route denied",request(anonymous,"unknown")[0]==404)
        check("Path parameter bypass denied",request(anonymous,"read;ignored")[0] in {401,404})
        check("Anonymous write denied",request(anonymous,"operate",b"")[0]==401)
        # Wrong credentials and login CSRF are distinct checks.
        _,anon=client();code,body,_=request(anon,"login");csrf=re.search("name='csrf' value='([^']+)'",body)[1]
        check("Login CSRF required",request(anon,"login",{"username":"reader","password":credentials["reader"]})[0]==403)
        check("Wrong password denied",request(anon,"login",{"username":"reader","password":"incorrect","csrf":csrf})[0]==401)
        sessions={who:login(who) for who in credentials}
        for who,(_,opener,csrf) in sessions.items():
            check("Authorized read: "+who,request(opener,"read")[0]==200)
            check("Mutation CSRF required: "+who,request(opener,"operate",b"")[0]==403)
            expected=403 if who=="reader" else 204
            check("Operator role boundary: "+who,request(opener,"operate",b"",csrf)[0]==expected)
            check("Administrator role boundary: "+who,request(opener,"admin",b"",csrf)[0]==(204 if who=="admin" else 403))
            check("CDI boundary cannot bypass role: "+who,request(opener,"boundary",b"",csrf)[0]==expected)
        check("Authorized service mutations produce exactly five effects",request(sessions["reader"][1],"read")[1].split("|")[-1]=="5")
        check("Token from another identity is rejected",request(sessions["operator"][1],"operate",b"",sessions["admin"][2])[0]==403)
        jar,reader,csrf=sessions["reader"]
        # Counter is fixture-only downstream observation, not candidate DB/JMS proof.
        before=request(reader,"read")[1].split("|")[-1]
        check("Reader direct write rejected",request(reader,"operate",b"",csrf)[0]==403)
        after=request(reader,"read")[1].split("|")[-1]
        check("Denied fixture mutation has no downstream counter effect",before==after)
        stale=client()[1];stale.addheaders=[("Cookie","JSESSIONID="+next(c.value for c in jar if c.name=="JSESSIONID"))]
        check("Logout rejects missing CSRF",request(reader,"logout",b"")[0]==403)
        check("Logout succeeds",request(reader,"logout",b"",csrf)[0]==204)
        check("Logged out session cannot read",request(stale,"read")[0]==401)
        check("Logged out session cannot mutate",request(stale,"operate",b"",csrf)[0]==401)
        _,expiry,token=login("reader")
        # True server idle expiration, no request refreshes this session while waiting.
        print("Checking real server idle expiration (about 75 seconds)",flush=True)
        for _ in range(5):time.sleep(15)
        check("Expired session cannot read",request(expiry,"read")[0]==401)
        check("Expired session cannot mutate",request(expiry,"operate",b"",token)[0]==401)
        report["status"]="PASS"
    except Exception as error:
        report["error_type"]=type(error).__name__
        raise
    finally:
        if not finalize(container,[users,roles],report):
            raise RuntimeError("Fixture cleanup incomplete; inspect sanitized results")

if __name__=="__main__":main()
