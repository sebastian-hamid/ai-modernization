const {chromium,request:requestFactory}=require("playwright");
const fs=require("fs");
const cfg=JSON.parse(fs.readFileSync("/run/credentials.json","utf8"));
const base=cfg.base;
const navigationActions=require("./navigation-actions.json");const actionProofs={};const claimedCargoProofs={};
const checks=[];const failures=[];const pageSemantics={};const socketObservations={};const socketTrace=[];const disconnectEvidence={};let abruptPeer=null;let witnessForDiagnostics=null;let stage="initialize";let navigation=null;
function check(name,ok){stage=name;checks.push({name,passed:!!ok});if(!ok)throw new Error(name);}
async function traceSocket(label,actor){
 if(!actor)return;
 const state=await actor.page.evaluate(()=>({readyState:window.liveSocket?.readyState,closed:window.socketClosed,frameCount:window.framesReceived?.length,lastFrameLocation:window.framesReceived?.at(-1)?.lastKnownLocationCode,openedAt:window.socketOpenedAt,close:window.socketCloseInfo??null}));
 socketTrace.push({label,role:actor.who,at:Date.now(),...state});
}
(async()=>{
 const browser=await chromium.launch({headless:true});let replayClient;
 try {
  replayClient=await requestFactory.newContext();
  const anon=await browser.newContext();const ap=await anon.newPage();
  await ap.goto(base+"admin/dashboard.xhtml");
  check("Anonymous page goes to login",ap.url().endsWith("/login"));
  check("Login does not leak cargo",!(await ap.textContent("body")).includes("ABC123"));
  async function login(who){
   const context=await browser.newContext();const page=await context.newPage();
   page.on("response",r=>{if(r.request().isNavigationRequest())navigation={path:new URL(r.url()).pathname,status:r.status()};});
   page.on("pageerror",()=>failures.push("pageerror:"+who));
   page.on("response",r=>{if(r.status()>=400 && r.url().includes("/jakarta.faces.resource/"))failures.push(new URL(r.url()).pathname);});
   await page.goto(base+"login");
   await page.getByLabel("Username").fill(who);
   await page.getByLabel("Password").fill(cfg.credentials[who]);
   await page.getByRole("button",{name:"Sign in"}).click();
   await page.waitForURL(base+"session");
   const identity=JSON.parse(await page.textContent("body"));
   const role={reader:"Reader",operator:"Operator",admin:"Administrator"}[who];
   check("Browser login "+who,identity.principal===who && identity.roles.includes(role));
   return {context,page,who,identity};
  }

  const aliasesRead=["public/track.xhtml","admin/map.xhtml","admin/mapFrame.html"];
  const aliasesWrite=["admin/selectItinerary.xhtml","eventLogger/eventLogger.xhtml","eventLogger/root.xhtml","booking/booking.xhtml","booking/booking-date.xhtml","booking/booking-destination.xhtml"];
  const home=await anon.request.get(base);
  check("Public home links to current tracking view",home.status()===200 && (await home.text()).includes("admin/track.xhtml"));
  for(const path of [...aliasesRead,...aliasesWrite]){
   const response=await anon.request.get(base+path+"?trackingId=UNKNOWN",{maxRedirects:0});
   check("Authentication precedes legacy lookup "+path,response.status()===303 && response.headers().location.endsWith("/login"));
  }
  async function readViews(actor){
   const previousViewport=actor.page.viewportSize();await actor.page.setViewportSize({width:390,height:844});
   const response=await actor.context.request.get(base+"rest/cargo");const cargos=await response.json();
   for(const [path,heading,kind] of [["listRouted","Routed cargo","routed"],["listNotRouted","Unrouted cargo","unrouted"],["listClaimed","Claimed cargo","claimed"]]){
    await actor.page.goto(base+"admin/"+path+".xhtml");
    await actor.page.getByRole("heading",{name:heading,exact:true}).waitFor();
    const actual=(await actor.page.locator("#cargos tbody tr td:first-child a").allTextContents()).sort();
    const expected=cargos.filter(c=>kind==="claimed"?c.transportStatus==="CLAIMED":kind==="unrouted"?c.routingStatus==="NOT_ROUTED":c.routingStatus!=="NOT_ROUTED"&&c.transportStatus!=="CLAIMED").map(c=>c.trackingId).sort();
    check("Filtered list exact persisted partition "+actor.who+" "+kind,JSON.stringify(actual)===JSON.stringify(expected));
    if(expected.length===0){await actor.page.getByText("No cargo matches this view.",{exact:true}).waitFor();check("Empty filtered list controlled "+kind,true);}
    check("Filtered list fits viewport "+actor.who+" "+kind,await actor.page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   }
   await actor.page.goto(base+"admin/about.xhtml");await actor.page.getByRole("heading",{name:"Cargo workflows",exact:true}).waitFor();
   check("Protected About workflow page "+actor.who,true);
   if(previousViewport)await actor.page.setViewportSize(previousViewport);
  }
  for(const path of ["admin/about.xhtml","admin/listRouted.xhtml","admin/listNotRouted.xhtml","admin/listClaimed.xhtml"]){
   await ap.goto(base+path);check("Anonymous filtered/About page goes to login "+path,ap.url().endsWith("/login")&&!(await ap.textContent("body")).includes("ABC123"));
  }
  await ap.goto(base+"public/about.xhtml");await ap.getByText("Tracking requires sign-in.",{exact:true}).waitFor();check("Public About accurately explains login",!(await ap.textContent("body")).includes("ABC123"));
  async function liveAliases(actor){
   const role={reader:"Reader",operator:"Operator",admin:"Administrator"}[actor.who];
   for(const [surface,path] of [["PAGE-09","admin/map.xhtml"],["PAGE-10","admin/mapFrame.html"]]){
    const page=await actor.context.newPage();
    try{
     const response=await page.goto(base+path);
     await page.locator("#live-status").getByText("Live",{exact:true}).waitFor();
     await page.locator('tr[data-tracking-id="ABC123"]').waitFor();
     check("Alias browser data and socket live "+surface+" "+role,response.status()===200 && new URL(page.url()).pathname==="/cargo-tracker/admin/live.xhtml");
     pageSemantics[surface+"::"+role+"::active"]={principal:actor.identity.principal,roles:actor.identity.roles,source_path:"/"+path,final_path:"/cargo-tracker/admin/live.xhtml",status:response.status(),cargo_observed:"ABC123",socket_live:true};
    }finally{await page.close();}
   }
  }
  for(const [path,heading] of [["error.xhtml","Request could not be completed"],["error_404.xhtml","Page not found"]]){
   await ap.goto(base+path+"?message=%3Cscript%3Ebad%3C/script%3E&next=https://untrusted.example");
   await ap.getByRole("heading",{name:heading,exact:true}).waitFor();
   const body=await ap.textContent("body");
   check("Generic error page ignores unsafe query "+path,!body.includes("bad")&&!body.includes("untrusted.example")&&!body.includes("ABC123")&&await ap.locator("script").count()===0);
  }
  function navigationTarget(url,target){
   const parsed=new URL(url);const expected=new URL(base+target);const keys=[...parsed.searchParams.keys()];
   if(parsed.origin!==expected.origin||parsed.pathname!==expected.pathname||new Set(keys).size!==keys.length)return false;
   for(const [key,value] of expected.searchParams)if(parsed.searchParams.getAll(key).length!==1||parsed.searchParams.get(key)!==value)return false;
   return keys.every(key=>expected.searchParams.has(key)||(key==="jfwid"&&parsed.searchParams.get(key).length>0));
  }
  async function navigationProofs(actor){
   const who=actor?actor.who:"anonymous";const role=actor?{reader:"Reader",operator:"Operator",admin:"Administrator"}[who]:"anonymous";
   const context=actor?actor.context:anon;
   for(const spec of navigationActions){
    const page=await context.newPage();
    try{
     const allowed=role==="anonymous"?spec.anonymous:spec.allowed_roles.includes(role);
     const source=role==="anonymous"&&!spec.anonymous?"index.xhtml":spec.source_page;
     await page.goto(base+source);
     const link=page.getByRole("link",{name:spec.label,exact:true});
     const visible=await link.count()===1;
     const driver=allowed||visible?"click":"direct";
     check("Navigation control "+spec.id+" "+role,allowed?visible:!visible||["ACTION-01","ACTION-03","ACTION-04"].includes(spec.id));
     let response;
     if(driver==="click"){
      const href=new URL(await link.getAttribute("href"),page.url());
      navigation={action:spec.id,actor:role,path:href.pathname.replace(/;jsessionid=[^/;]*/gi,";jsessionid=[redacted]"),query_keys:[...href.searchParams.keys()],origin_matches:href.origin===new URL(base).origin};
      check("Navigation exact local href "+spec.id+" "+role,navigationTarget(href.href,spec.target));
      [response]=await Promise.all([page.waitForResponse(r=>r.request().isNavigationRequest()&&navigationTarget(r.url(),spec.target)),link.click()]);
     }else response=await page.goto(base+spec.target);
     // goto returns the final login page after303; capture the actual protected request.
     let first=response;
     while(first.request().redirectedFrom())first=await first.request().redirectedFrom().response();
     const original=new URL(first.url());
     const proof={supported:true,status:first.status(),target:spec.target,source_page:source,driver,action_executed:true,control_hidden:!visible,target_origin_verified:original.origin===new URL(base).origin,actual_target_path:original.pathname,query_keys:[...original.searchParams.keys()],tracking_id:original.searchParams.get("trackingId")};
     if(actor)proof.identity={server_verified:true,principal:actor.identity.principal,roles:actor.identity.roles};
     if(allowed){
      await page.getByRole("heading",{name:spec.heading,exact:true}).waitFor();
      check("Navigation destination "+spec.id+" "+role,new URL(page.url()).pathname==="/cargo-tracker/"+spec.target.split("?")[0]&&first.status()===200);
      if(spec.kind==="live"){
       await page.locator("#live-status").getByText("Live",{exact:true}).waitFor();
       await page.locator('tr[data-tracking-id="ABC123"]').waitFor();proof.socket_live=true;proof.cargo_observed="ABC123";
      }else if(spec.kind==="list"){
       await page.getByRole("link",{name:"ABC123",exact:true}).waitFor();proof.cargo_observed="ABC123";
      }else if(spec.kind==="routed-detail"){
       proof.cargo_observed=await page.locator("#trackingId").textContent();
       proof.routing_status=await page.locator("#routingStatus").textContent();
       proof.transport_status=await page.locator("dt").filter({hasText:/^Status$/}).locator("xpath=following-sibling::dd[1]").textContent();
       check("Routed list opens actual unclaimed cargo "+role,proof.cargo_observed==="ABC123"&&proof.routing_status==="ROUTED"&&["NOT_RECEIVED","IN_PORT","ONBOARD_CARRIER"].includes(proof.transport_status));
      }else if(spec.kind==="booking"){
       await page.getByLabel("Origin",{exact:true}).waitFor();await page.getByLabel("Destination",{exact:true}).waitFor();proof.form_observed=true;
      }else if(spec.kind==="lookup"){
       await page.getByLabel("Tracking ID",{exact:true}).waitFor();proof.form_observed=true;
      }
      proof.semantic_success=true;
      if(spec.anonymous)proof.protected_payload_absent=!(await page.textContent("body")).includes("ABC123")&&!(await page.textContent("body")).includes("DEF789");
     }else{
      const body=await page.textContent("body");proof.protected_payload_absent=!body.includes("ABC123")&&!body.includes("DEF789")&&!body.includes("Hong Kong");
      proof.redirect_is_configured_login=first.status()===303&&new URL(first.headers().location,base).href===base+"login"&&page.url()===base+"login";
      check("Navigation denial "+spec.id+" "+role,(role==="anonymous"?proof.redirect_is_configured_login:first.status()===403)&&proof.protected_payload_absent);
     }
     actionProofs[spec.id+"::"+role+"::active"]=proof;
    }finally{await page.close();}
   }
  }
  await navigationProofs(null);
  const reader=await login("reader");
  await navigationProofs(reader);
  await liveAliases(reader);
  await readViews(reader);

  await reader.page.goto(base+"admin/track.xhtml");
  await reader.page.getByLabel("Tracking ID",{exact:true}).fill("UNKNOWN");
  await reader.page.getByRole("button",{name:"Track cargo",exact:true}).click();
  await reader.page.getByText("Cargo not found.",{exact:true}).waitFor();
  check("Tracking form unknown cargo controlled",reader.page.url().includes("/admin/track.xhtml"));
  await reader.page.getByLabel("Tracking ID",{exact:true}).fill("<script>");
  await reader.page.getByRole("button",{name:"Track cargo",exact:true}).click();
  await reader.page.getByText("Enter a valid tracking ID.",{exact:true}).waitFor();
  check("Tracking form malformed ID controlled",true);
  await reader.page.getByLabel("Tracking ID",{exact:true}).fill("ABC123");
  await reader.page.getByRole("button",{name:"Track cargo",exact:true}).click();
  await reader.page.waitForURL(/admin\/show.xhtml\?trackingId=ABC123/);
  check("Tracking form valid cargo navigation",await reader.page.locator("#trackingId").textContent()==="ABC123");
  for(const path of ["admin/track.xhtml?trackingId=UNKNOWN","admin/track.xhtml?trackingId=%3Cscript%3E","public/track.xhtml?trackingId=UNKNOWN","public/track.xhtml?trackingId=ABC123&trackingId=DEF789","public/track.xhtml?trackingId=%3Cscript%3E"]){
   const response=await reader.context.request.get(base+path);
   check("Tracking direct invalid ID controlled "+path,response.status()===404);
  }
  const publicTrack=await reader.context.request.get(base+"public/track.xhtml?trackingId=ABC123");
  check("Legacy tracking reaches actual cargo",publicTrack.status()===200 && (await publicTrack.text()).includes('id="trackingId">ABC123'));
  const noId=await reader.context.request.get(base+"public/track.xhtml");
  check("Legacy tracking without ID shows lookup",noId.status()===200 && (await noId.text()).includes("Tracking ID"));
  for(const path of ["admin/map.xhtml","admin/mapFrame.html"]){
   const response=await reader.context.request.get(base+path+"?redirect=https://untrusted.example",{maxRedirects:0});
   check("Fixed local legacy map redirect "+path,response.status()===303 && response.headers().location.endsWith("/admin/live.xhtml"));
   const target=await reader.context.request.get(base+path);
   check("Legacy map reaches supported live view "+path,target.status()===200 && (await target.text()).includes('id="live-cargos"'));
  }
  for(const path of aliasesWrite){
   const response=await reader.context.request.get(base+path+"?trackingId=%3Cscript%3E");
   check("Reader denied before legacy input handling "+path,response.status()===403);
  }

  await reader.page.goto(base+"admin/dashboard.xhtml");
  await reader.page.getByRole("heading",{name:"Cargo list",exact:true}).waitFor();
  check("Reader sees seeded cargo",await reader.page.getByRole("link",{name:"ABC123",exact:true}).count()===1);
  check("Reader does not see booking control",await reader.page.getByRole("link",{name:"Book cargo",exact:true}).count()===0);
  await reader.page.getByRole("link",{name:"ABC123",exact:true}).click();
  await reader.page.getByRole("heading",{name:"Cargo details",exact:true}).waitFor();
  check("Reader sees details",await reader.page.locator("#trackingId").textContent()==="ABC123");
  check("Reader does not see destination control",await reader.page.getByRole("link",{name:"Change destination"}).count()===0);
  check("Reader does not see routing control",await reader.page.getByRole("link",{name:"Assign route",exact:true}).count()===0);
  for(const path of ["admin/book.xhtml","admin/changeDestination.xhtml?trackingId=ABC123","admin/route.xhtml?trackingId=ABC123"]){
   const response=await reader.context.request.get(base+path);check("Reader direct denial "+path,response.status()===403);
  }
  for(const path of ["admin/show.xhtml","admin/show.xhtml?trackingId=UNKNOWN","admin/show.xhtml?trackingId=%3Cscript%3E"]){
   const response=await reader.context.request.get(base+path);check("Controlled invalid link "+path,response.status()===404);
  }
  const operator=await login("operator");await navigationProofs(operator);await liveAliases(operator);
  async function book(actor){
   const page=actor.page;
   await page.goto(base+"admin/book.xhtml");
   await page.getByLabel("Origin",{exact:true}).selectOption("CNHKG");
   await page.getByLabel("Destination",{exact:true}).selectOption("CNHKG");
   await page.getByLabel("Arrival deadline (YYYY-MM-DD)").fill("2030-12-31");
   await page.getByRole("button",{name:"Book cargo",exact:true}).click();
   await page.getByText("Choose different valid origin and destination locations.",{exact:true}).waitFor();
   check("Same-location booking rejected",page.url().includes("/admin/book.xhtml"));
   await page.getByLabel("Destination",{exact:true}).selectOption("FIHEL");
   await page.getByLabel("Arrival deadline (YYYY-MM-DD)").fill("2030-02-30");
   await page.getByRole("button",{name:"Book cargo",exact:true}).click();
   await page.getByText("Enter a valid arrival deadline in YYYY-MM-DD format.",{exact:true}).waitFor();
   check("Invalid calendar date rejected",page.url().includes("/admin/book.xhtml"));
   await page.getByLabel("Arrival deadline (YYYY-MM-DD)").fill("2030-12-31");
   await page.getByRole("button",{name:"Book cargo",exact:true}).click();
   await page.waitForURL(/admin\/show.xhtml\?trackingId=/);
   const id=await page.locator("#trackingId").textContent();
   check("Booking persists new tracking ID",/^[A-Z0-9]{8}$/.test(id));
   await page.getByRole("link",{name:"Change destination",exact:true}).click();
   await page.getByLabel("Destination",{exact:true}).selectOption("USNYC");
   await page.getByRole("button",{name:"Save destination",exact:true}).click();
   await page.waitForURL(/admin\/show.xhtml\?trackingId=/);
   check("Destination change persisted",(await page.locator("#destination").textContent()).includes("New York"));
   const read=await reader.context.request.get(base+"admin/show.xhtml?trackingId="+id);
   check("Independent Reader sees persisted destination",read.status()===200 && (await read.text()).includes("New York"));
   await routeCargo(actor,id);
   await readViews(actor);
   return id;
  }
  async function tableRows(table){
   return table.locator("tbody tr").evaluateAll(rows=>rows.map(row=>Array.from(row.cells).map(cell=>cell.textContent.trim())));
  }
  async function routeCargo(actor,id){
   const page=actor.page;
   await page.getByRole("link",{name:"Assign route",exact:true}).click();
   await page.getByRole("heading",{name:"Assign route",exact:true}).waitFor();
   check("Sample routing candidates rendered",await page.locator('select[id="routing:choice"] option').count()>1);
   await page.getByRole("button",{name:"Assign selected route",exact:true}).click();
   await page.getByText("Choose a valid route.",{exact:true}).waitFor();
   check("Missing route selection rejected",page.url().includes("/admin/route.xhtml"));
   const csrf=await page.locator('input[name="csrf"]').inputValue();
   const state=await page.locator('input[name="jakarta.faces.ViewState"]').first().inputValue();
   const routeUrl=base+"admin/route.xhtml?trackingId="+id;
   const readerCsrf=(await (await reader.context.request.get(base+"session")).json()).csrf;
   const denied=await reader.context.request.post(routeUrl,{form:{"csrf":readerCsrf,"routing":"routing","routing:choice":"0","routing:submit":"","jakarta.faces.ViewState":state}});
   check("Reader forged route assignment denied",denied.status()===403);
   const noToken=await actor.context.request.post(routeUrl,{form:{"routing":"routing","routing:choice":"0","routing:submit":"","jakarta.faces.ViewState":state}});
   check("Route assignment requires CSRF",noToken.status()===403);
   const tampered=await actor.context.request.post(routeUrl,{form:{"csrf":csrf,"routing":"routing","routing:choice":"99999","routing:submit":"","jakarta.faces.ViewState":state}});
   check("Unknown route index rejected",tampered.status()===200 && (await tampered.text()).includes("Value is not valid"));
   let observed=await reader.context.request.get(base+"admin/show.xhtml?trackingId="+id);
   check("Denied selections leave cargo unrouted",(await observed.text()).includes('id="routingStatus">NOT_ROUTED'));
   // A different real view changes destination while the original candidate view remains open.
   await page.reload();
   const other=await actor.context.newPage();
   await other.goto(base+"admin/changeDestination.xhtml?trackingId="+id);
   await other.getByLabel("Destination",{exact:true}).selectOption("FIHEL");
   await other.getByRole("button",{name:"Save destination",exact:true}).click();
   await other.waitForURL(/admin\/show.xhtml\?trackingId=/);
   await other.close();
   await page.getByLabel("Route",{exact:true}).selectOption("0");
   await page.getByRole("button",{name:"Assign selected route",exact:true}).click();
   await page.getByText("The selected route no longer matches this cargo. Request routes again.",{exact:true}).waitFor();
   check("Stale route after destination change rejected",page.url().includes("/admin/route.xhtml"));
   observed=await reader.context.request.get(base+"admin/show.xhtml?trackingId="+id);
   check("Stale selection does not assign old itinerary",(await observed.text()).includes('id="routingStatus">NOT_ROUTED'));
   await page.getByRole("link",{name:"Request fresh routes",exact:true}).click();
   const label=await page.locator('select[id="routing:choice"] option[value="0"]').textContent();
   const expectedLegs=Number(label.match(/\((\d+) legs\)/)[1]);
   const selectedRows=await tableRows(page.locator("table.route-candidate").first());
   await page.getByLabel("Route",{exact:true}).selectOption("0");
   await page.getByRole("button",{name:"Assign selected route",exact:true}).click();
   await page.waitForURL(/admin\/show.xhtml\?trackingId=/);
   check("Real route assignment is ROUTED",await page.locator("#routingStatus").textContent()==="ROUTED");
   check("Selected itinerary leg count persisted",await page.locator("#itinerary tbody tr").count()===expectedLegs);
   check("Exact selected voyage/location/time sequence persisted",JSON.stringify(await tableRows(page.locator("#itinerary")))===JSON.stringify(selectedRows));
   observed=await reader.context.request.get(base+"admin/show.xhtml?trackingId="+id);
   const html=await observed.text();
   check("Separate Reader sees persisted route",observed.status()===200 && html.includes('id="routingStatus">ROUTED') && html.includes('id="itinerary"'));
   await reader.page.goto(base+"admin/show.xhtml?trackingId="+id);
   check("Separate Reader verifies exact itinerary sequence",JSON.stringify(await tableRows(reader.page.locator("#itinerary")))===JSON.stringify(selectedRows));
   await page.getByRole("link",{name:"Assign route",exact:true}).click();
   await page.getByRole("heading",{name:"Assign route",exact:true}).waitFor();
   const replacementLabel=await page.locator('select[id="routing:choice"] option[value="0"]').textContent();
   const replacementLegs=Number(replacementLabel.match(/\((\d+) legs\)/)[1]);
   const replacementRows=await tableRows(page.locator("table.route-candidate").first());
   await page.getByLabel("Route",{exact:true}).selectOption("0");
   await page.getByRole("button",{name:"Assign selected route",exact:true}).click();
   await page.waitForURL(/admin\/show.xhtml\?trackingId=/);
   check("Rerouting existing cargo persists owned collection",await page.locator("#routingStatus").textContent()==="ROUTED" && await page.locator("#itinerary tbody tr").count()===replacementLegs);
   check("Exact replacement route sequence persisted",JSON.stringify(await tableRows(page.locator("#itinerary")))===JSON.stringify(replacementRows));
  }
  const id=await book(operator);
  const form=await operator.context.request.get(base+"admin/book.xhtml");
  const html=await form.text();const view=html.match(/name="jakarta.faces.ViewState"[^>]*value="([^"]+)"/);
  check("Real Faces ViewState rendered",!!view);
  const readerToken=(await (await reader.context.request.get(base+"session")).json()).csrf;
  const forged=await reader.context.request.post(base+"admin/book.xhtml",{form:{"csrf":readerToken,"booking":"booking","booking:origin":"CNHKG","booking:destination":"FIHEL","booking:deadline":"2030-12-31","booking:submit":"","jakarta.faces.ViewState":view[1]}});
  check("Reader forged booking POST denied",forged.status()===403);
  const noCsrf=await operator.context.request.post(base+"admin/book.xhtml",{form:{"booking":"booking","booking:submit":"","jakarta.faces.ViewState":view[1]}});
  check("Missing CSRF booking POST denied",noCsrf.status()===403);

  const admin=await login("admin");await navigationProofs(admin);await liveAliases(admin);await book(admin);
  for(const actor of [operator,admin]){
   for(const path of aliasesWrite){
    const response=await actor.context.request.get(base+path+(path.includes("selectItinerary")?"?trackingId="+id:""));
    const heading=path.includes("selectItinerary")?"Assign route":path.startsWith("booking/")?"Book cargo":"Report handling";
    check("Authorized legacy navigation "+path,response.status()===200 && (await response.text()).includes("<h1>"+heading+"</h1>"));
   }
   for(const path of ["admin/selectItinerary.xhtml","admin/selectItinerary.xhtml?trackingId=UNKNOWN","admin/selectItinerary.xhtml?trackingId=%3Cscript%3E","admin/show.xhtml","admin/show.xhtml?trackingId=UNKNOWN","admin/changeDestination.xhtml","admin/changeDestination.xhtml?trackingId=UNKNOWN","admin/route.xhtml","admin/route.xhtml?trackingId=UNKNOWN"]){
    const response=await actor.context.request.get(base+path);
    check("Authorized invalid direct link controlled "+path,response.status()===404);
   }
   const token=(await (await actor.context.request.get(base+"session")).json()).csrf;
   for(const path of aliasesWrite){
    const noCsrf=await actor.context.request.post(base+path,{form:{trackingId:id},maxRedirects:0});
    check("Retired callback requires CSRF "+path,noCsrf.status()===403);
    const post=await actor.context.request.post(base+path,{form:{csrf:token,trackingId:id},maxRedirects:0});
    check("Retired callback never replays mutations "+path,post.status()===405);
   }
  }

  await operator.page.goto(base+"admin/book.xhtml");
  await operator.page.getByLabel("Origin",{exact:true}).selectOption("CNHKG");
  await operator.page.getByLabel("Destination",{exact:true}).selectOption("FIHEL");
  await operator.page.getByLabel("Arrival deadline (YYYY-MM-DD)").fill("2000-01-01");
  await operator.page.getByRole("button",{name:"Book cargo",exact:true}).click();
  await operator.page.waitForURL(/admin\/show.xhtml\?trackingId=/);
  await operator.page.getByRole("link",{name:"Assign route",exact:true}).click();
  await operator.page.getByText("No sample routes meet this cargo's arrival deadline.",{exact:true}).waitFor();
  check("No candidates for expired deadline handled",await operator.page.getByRole("button",{name:"Assign selected route",exact:true}).count()===0);
  const readerMobile=await reader.context.request.get(base+"mobile.xhtml");
  check("Reader direct handling UI denied",readerMobile.status()===403);
  for(const actor of [operator,admin]){
   await actor.page.setViewportSize({width:390,height:844});
   await actor.page.goto(base+"mobile.xhtml");
   await actor.page.getByRole("heading",{name:"Report handling",exact:true}).waitFor();
   check("Mobile handling form fits viewport",await actor.page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));
   const mobileState=await actor.page.locator('input[name="jakarta.faces.ViewState"]').first().inputValue();
   const readerMobileToken=(await (await reader.context.request.get(base+"session")).json()).csrf;
   const readerPost=await reader.context.request.post(base+"mobile.xhtml",{form:{"csrf":readerMobileToken,"handling":"handling","handling:submit":"","jakarta.faces.ViewState":mobileState}});
   check("Reader forged mobile POST denied",readerPost.status()===403);
   const mobileNoToken=await actor.context.request.post(base+"mobile.xhtml",{form:{"handling":"handling","handling:submit":"","jakarta.faces.ViewState":mobileState}});
   check("Mobile mutation requires CSRF",mobileNoToken.status()===403);
   await actor.page.getByLabel("Cargo",{exact:true}).selectOption(id);
   await actor.page.getByLabel("Event",{exact:true}).selectOption("LOAD");
   const handlingLocation=actor===operator?"USCHI":"DEHAM";
   await actor.page.getByLabel("Location",{exact:true}).selectOption(handlingLocation);
   await actor.page.getByLabel("Completion time (YYYY-MM-DD HH:mm)").fill("2032-02-30 10:00");
   await actor.page.getByRole("button",{name:"Submit handling report",exact:true}).click();
   await actor.page.getByText("Enter a valid completion time in YYYY-MM-DD HH:mm format.",{exact:true}).waitFor();
   check("Mobile invalid calendar rejected",true);
   await actor.page.getByLabel("Completion time (YYYY-MM-DD HH:mm)").fill(actor===operator?"2032-02-01 10:00":"2032-02-03 10:00");
   await actor.page.getByRole("button",{name:"Submit handling report",exact:true}).click();
   await actor.page.getByText("Choose a voyage for LOAD or UNLOAD.",{exact:true}).waitFor();
   check("Mobile missing required voyage rejected",true);
   await actor.page.getByLabel("Event",{exact:true}).selectOption("CUSTOMS");
   await actor.page.getByRole("button",{name:"Submit handling report",exact:true}).click();
   await actor.page.getByText("Accepted for processing. Check cargo details for the result.",{exact:true}).waitFor();
   check("Mobile handling accepts asynchronous submission",true);
   await reader.context.request.get(base+"session");
   let changed=false;
   for(let retry=0;retry<40;retry++){const response=await reader.context.request.get(base+"rest/cargo");const cargos=await response.json();if(cargos.find(c=>c.trackingId===id).lastKnownLocation===handlingLocation){changed=true;break;}await actor.page.waitForTimeout(250);}
   check("Mobile handling actual persistence readback",changed);
   await actor.page.getByLabel("Event",{exact:true}).selectOption("LOAD");
   await actor.page.getByLabel("Voyage (required for LOAD/UNLOAD)").selectOption("0100S");
   await actor.page.getByLabel("Completion time (YYYY-MM-DD HH:mm)").fill(actor===operator?"2032-02-02 10:00":"2032-02-04 10:00");
   await actor.page.getByRole("button",{name:"Submit handling report",exact:true}).click();
   await actor.page.getByText("Accepted for processing. Check cargo details for the result.",{exact:true}).waitFor();
   check("Mobile LOAD with voyage accepted",true);
   let loaded=false;
   for(let retry=0;retry<40;retry++){const response=await reader.context.request.get(base+"rest/cargo");const cargo=(await response.json()).find(c=>c.trackingId===id);if(cargo.transportStatus==="ONBOARD_CARRIER"&&cargo.lastKnownLocation===handlingLocation){loaded=true;break;}await actor.page.waitForTimeout(250);}
   check("Mobile LOAD actually changes transport state",loaded);
  }

  for(const [event,date] of [["UNLOAD","2032-02-05 10:00"],["CLAIM","2032-02-06 10:00"]]){
   const token=(await (await admin.context.request.get(base+"session")).json()).csrf;
   const result=await admin.context.request.post(base+"rest/handling/reports",{headers:{"X-CSRF-Token":token},data:{trackingId:id,eventType:event,unLocode:"FIHEL",completionTime:date,...(event==="UNLOAD"?{voyageNumber:"0100S"}:{})}});
   check("Actual "+event+" for claimed-list fixture accepted",result.status()===204);
   let completed=false;
   for(let retry=0;retry<40;retry++){const cargo=(await (await reader.context.request.get(base+"rest/cargo")).json()).find(c=>c.trackingId===id);if(cargo.transportStatus===(event==="CLAIM"?"CLAIMED":"IN_PORT")&&cargo.lastKnownLocation==="FIHEL"){completed=true;break;}await admin.page.waitForTimeout(250);}
   check("Actual "+event+" fixture persisted",completed);
  }
  for(const actor of [reader,operator,admin])await readViews(actor);
  const claimedList="admin/listClaimed.xhtml";
  const claimedTarget="admin/show.xhtml?trackingId="+id;
  const claimedSnapshotResponse=await reader.context.request.get(base+"rest/cargo");
  check("Claimed cargo independent snapshot available",claimedSnapshotResponse.status()===200);
  const claimedCargo=(await claimedSnapshotResponse.json()).find(cargo=>cargo.trackingId===id);
  check("Selected cargo is persistently claimed",claimedCargo?.transportStatus==="CLAIMED");
  function claimedNavigationProof(response,source,driver){
   const url=new URL(response.url());
   return {supported:true,status:response.status(),source_page:source,driver,action_executed:true,
    target_origin_verified:url.origin===new URL(base).origin,actual_target_path:url.pathname,
    query_keys:[...url.searchParams.keys()],tracking_id:url.searchParams.get("trackingId"),
    current_navigation_driver:"browser-claimed-cargo-v1"};
  }
  for(const actor of [reader,operator,admin]){
   const role={reader:"Reader",operator:"Operator",admin:"Administrator"}[actor.who];
   const page=await actor.context.newPage();
   try{
    const listResponse=await page.goto(base+claimedList);
    await page.getByRole("heading",{name:"Claimed cargo",exact:true}).waitFor();
    const link=page.locator("#cargos").getByRole("link",{name:id,exact:true});
    check("Claimed list exposes exactly the selected cargo link "+role,listResponse.status()===200&&navigationTarget(page.url(),claimedList)&&await link.count()===1);
    check("Claimed cargo link identifies exact local target "+role,navigationTarget(new URL(await link.getAttribute("href"),page.url()).href,claimedTarget));
    const [response]=await Promise.all([page.waitForResponse(r=>r.request().isNavigationRequest()&&navigationTarget(r.url(),claimedTarget)),link.click()]);
    await page.getByRole("heading",{name:"Cargo details",exact:true}).waitFor();
    check("Claimed cargo click reached the selected details "+role,response.status()===200&&navigationTarget(page.url(),claimedTarget));
    const detail=label=>page.getByText(label,{exact:true}).and(page.locator("dt")).locator("xpath=following-sibling::dd[1]").textContent();
    const displayed={trackingId:await page.locator("#trackingId").textContent(),originName:(await detail("Origin")).trim(),
     destinationName:(await page.locator("#destination").textContent()).trim(),routingStatus:await page.locator("#routingStatus").textContent(),
     transportStatus:await detail("Status")};
    const fields=["trackingId","originName","destinationName","routingStatus","transportStatus"];
    check("Claimed cargo details match independent persisted values "+role,fields.every(field=>displayed[field]===claimedCargo[field])&&(await detail("Arrival deadline")).trim().split(/\s+/)[0]==="12/31/2030");
    claimedCargoProofs["CURRENT::ACTION-10::"+role+"::active"]={...claimedNavigationProof(response,claimedList,"click"),
     identity:{server_verified:true,principal:actor.identity.principal,roles:actor.identity.roles},semantic_success:true,
     selected_cargo_verified:true,persisted_details_verified:true};
   }finally{await page.close();}
  }
  const claimedLanding=await ap.goto(base+"index.xhtml");
  const claimedMarkers=[id,claimedCargo.originName,claimedCargo.destinationName,"Cargo details","Claimed cargo"];
  const claimedPayloadAbsent=body=>!claimedMarkers.some(marker=>body.includes(marker));
  check("Claimed cargo hidden on public landing",claimedLanding.status()===200&&claimedPayloadAbsent(await ap.textContent("body"))&&await ap.getByRole("link",{name:id,exact:true}).count()===0);
  const anonymousClaimedList=await anon.request.get(base+claimedList,{maxRedirects:0});
  const anonymousClaimedDetails=await anon.request.get(base+claimedTarget,{maxRedirects:0});
  const configuredLogin=response=>response.status()===303&&new URL(response.headers().location,base).href===base+"login";
  const claimedListDenied=configuredLogin(anonymousClaimedList)&&claimedPayloadAbsent(await anonymousClaimedList.text());
  const claimedDetailsDenied=configuredLogin(anonymousClaimedDetails)&&claimedPayloadAbsent(await anonymousClaimedDetails.text());
  check("Anonymous claimed cargo list and direct details deny without payload",claimedListDenied&&claimedDetailsDenied);
  claimedCargoProofs["CURRENT::ACTION-10::anonymous::active"]={...claimedNavigationProof(anonymousClaimedDetails,"index.xhtml","direct"),
   protected_payload_absent:true,redirect_is_configured_login:true,claimed_list_denied:true};
  await operator.page.setViewportSize({width:390,height:844});
  await operator.page.goto(base+"admin/show.xhtml?trackingId="+id);
  check("Cargo details fit mobile viewport",await operator.page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));
  const malicious=await ap.request.get(base+"jakarta.faces.resource/core.js.xhtml?ln=primefaces&pfdrid=forged");
  check("Dynamic resource bypass denied",malicious.status()===404);
  const roles={reader:"Reader",operator:"Operator",admin:"Administrator"};
  const noSocketPayload=body=>!["trackingId","ABC123","DEF789","transportStatus","originName"].some(marker=>body.includes(marker));
  const nativeIdentity=actor=>({server_verified:true,principal:actor.identity.principal,roles:actor.identity.roles});
  async function saveSocketCookie(actor){
   const cookie=(await actor.context.cookies(base)).find(c=>c.name==="JSESSIONID");
   check("Saved native socket cookie "+actor.who,!!cookie);return "JSESSIONID="+cookie.value;
  }
  async function revokedSocket(actor,state,closed,noFrames){
   const identity=await replayClient.get(base+"session",{headers:{Cookie:actor.savedCookie}});
   check("Saved socket cookie identity revoked "+actor.who+" "+state,identity.status()===401);
   const denial=await replayClient.get(base+"tracking?connection="+require("crypto").randomUUID(),{headers:{...wsHeaders,Cookie:actor.savedCookie}});
   const absent=noSocketPayload(await denial.text());
   check("Saved cookie upgrade denied "+actor.who+" "+state,denial.status()===401&&absent);
   check("Closed socket receives no post-revocation frame "+actor.who+" "+state,closed&&noFrames);
   return {supported:true,status:denial.status(),upgraded:false,protected_payload_absent:absent,identity:nativeIdentity(actor),authenticated_before_revocation:true,revocation_verified:true,existing_socket_closed:closed,post_revocation_frame_received:!noFrames,stale_cookie_replay_verified:true};
  }
  const wsHeaders={"Upgrade":"websocket","Connection":"Upgrade","Sec-WebSocket-Version":"13","Sec-WebSocket-Key":Buffer.from("0123456789abcdef").toString("base64"),"Origin":new URL(base).origin};
  let denied=await replayClient.get(base+"tracking?connection="+require("crypto").randomUUID(),{headers:wsHeaders});
  check("Anonymous upgrade is HTTP401",denied.status()===401);
  socketObservations["WS-01::anonymous::active"]={supported:true,status:denied.status(),upgraded:false,protected_payload_absent:noSocketPayload(await denied.text())};
  async function openAbruptPeer(cookie){
   const crypto=require("crypto");const key=crypto.randomBytes(16).toString("base64");
   return await new Promise((resolve,reject)=>{
    const req=require("http").request(base+"tracking?connection="+crypto.randomUUID(),{headers:{...wsHeaders,"Sec-WebSocket-Key":key,Cookie:cookie}});
    req.setTimeout(10000,()=>req.destroy(new Error("Upgrade timeout")));
    req.on("error",reject);req.on("response",response=>{response.resume();reject(new Error("Upgrade rejected"));});
    req.on("upgrade",(response,socket,head)=>{
     const expected=crypto.createHash("sha1").update(key+"258EAFA5-E914-47DA-95CA-C5AB0DC85B11").digest("base64");
     if(response.statusCode!==101||response.headers["sec-websocket-accept"]!==expected){socket.destroy();reject(new Error("Invalid upgrade"));return;}
     socket.setTimeout(0);const peer={socket,bytes:head.toString("utf8"),reset:false};
     socket.on("data",data=>{peer.bytes+=data.toString("utf8");});
     socket.on("error",()=>{});resolve(peer);
    });req.end();
   });
  }
  const sockets={};const livePages={};
  let snapshotReadyResolve,releaseSnapshot;
  const snapshotReady=new Promise(resolve=>snapshotReadyResolve=resolve);
  const snapshotRelease=new Promise(resolve=>releaseSnapshot=resolve);
  for(const who of ["reader","operator","admin"]){
   sockets[who]=await login(who);if(who==="admin")witnessForDiagnostics=sockets[who];sockets[who].savedCookie=await saveSocketCookie(sockets[who]);
   const bad=await sockets[who].context.request.get(base+"tracking?connection="+require("crypto").randomUUID(),{headers:{...wsHeaders,Origin:"https://untrusted.example"}});
   check("Authenticated wrong-origin upgrade denied "+who,bad.status()===403);
   socketObservations["WS-ORIGIN::"+roles[who]+"::active"]={supported:true,status:bad.status(),upgraded:false,protected_payload_absent:noSocketPayload(await bad.text()),identity:nativeIdentity(sockets[who])};
   await sockets[who].page.evaluate(url=>{
    window.framesReceived=[];window.socketClosed=false;window.socketOpenedAt=Date.now();window.socketCloseInfo=null;
    window.liveSocket=new WebSocket(url);
    window.liveSocket.onmessage=e=>window.framesReceived.push(JSON.parse(e.data));
    window.liveSocket.onclose=e=>{window.socketClosed=true;window.socketCloseInfo={code:e.code,reason:e.reason,at:Date.now()};};
   },base.replace("http:","ws:")+"tracking?connection="+require("crypto").randomUUID());
   await sockets[who].page.waitForFunction(()=>window.liveSocket.readyState===WebSocket.OPEN);
   check("Authorized upgrade "+who,true);
   livePages[who]=await sockets[who].context.newPage();
   livePages[who].on("pageerror",()=>failures.push("live-pageerror:"+who));
   livePages[who].on("response",r=>{if(r.status()>=400 && new URL(r.url()).pathname.includes("/resources/"))failures.push(new URL(r.url()).pathname);});
   if(who==="reader")await livePages[who].route(base+"rest/cargo",async route=>{
    const response=await route.fetch();snapshotReadyResolve();await snapshotRelease;await route.fulfill({response});
   });
   await livePages[who].goto(base+"admin/live.xhtml");
   if(who==="reader"){await snapshotReady;continue;}
   await livePages[who].locator("#live-status").getByText("Live",{exact:true}).waitFor();
   check("Live UI snapshot "+who,await livePages[who].locator('tr[data-tracking-id="DEF789"]').count()===1);
   check("Live UI has geographic marker "+who,await livePages[who].locator('#live-markers a[aria-label^="ABC123 "]').count()===1);
  }
  async function trigger(sequence){
   const producer=await (await replayClient.get(base+"session",{headers:{Cookie:sockets.admin.savedCookie}})).json();
   check("Producer native identity "+sequence,producer.principal==="admin"&&producer.roles.includes("Administrator"));
   const csrf=producer.csrf;await traceSocket("before-trigger-"+sequence,witnessForDiagnostics);
   const response=await replayClient.post(base+"rest/handling/reports",{headers:{Cookie:sockets.admin.savedCookie,"X-CSRF-Token":csrf},data:{trackingId:"DEF789",eventType:"CUSTOMS",unLocode:sequence===8?"USNYC":sequence%2===1?"SESTO":"FIHEL",completionTime:"2031-01-"+String(sequence).padStart(2,"0")+" 10:00"}});
   check("Actual handling trigger "+sequence,response.status()===204);
   await traceSocket("after-trigger-"+sequence,witnessForDiagnostics);
  }
  abruptPeer=await openAbruptPeer(sockets.admin.savedCookie);
  check("Abrupt peer performs validated native upgrade",true);
  await trigger(1);
  for(let n=0;n<100&&!abruptPeer.bytes.includes('"trackingId":"DEF789"');n++)await sockets.admin.page.waitForTimeout(100);
  check("Abrupt peer receives actual cargo before reset",abruptPeer.bytes.includes('"trackingId":"DEF789"'));
  check("TCP reset supported",typeof abruptPeer.socket.resetAndDestroy==="function");
  await new Promise(resolve=>{abruptPeer.socket.once("close",resolve);abruptPeer.socket.resetAndDestroy();});
  abruptPeer.reset=true;
  disconnectEvidence.abrupt_peer={validated_upgrade:true,actual_frame_before_reset:true,tcp_reset_without_close_frame:true};

  for(const who of ["reader","operator","admin"]){
   await sockets[who].page.waitForFunction(()=>window.framesReceived.some(e=>e.trackingId==="DEF789"));
   check("Actual authorized data frame "+who,true);
   socketObservations["WS-01::"+roles[who]+"::active"]={supported:true,status:101,semantic_success:true,authorized_frame_received:true,identity:nativeIdentity(sockets[who]),socket_open_observed:true};
   check("Legacy socket fields remain names "+who,await sockets[who].page.evaluate(()=>window.framesReceived.find(e=>e.trackingId==="DEF789").origin==="Hong Kong"));
   await livePages[who].locator('tr[data-tracking-id="DEF789"]').getByText("Stockholm",{exact:true}).waitFor();
   check("Actual live UI update "+who,true);
   check("Actual live marker moves "+who,await livePages[who].locator('#live-markers a[aria-label="DEF789 at SESTO"] circle').getAttribute("cx")==="396");
   if(who==="reader"){
    releaseSnapshot();await livePages.reader.locator("#live-status").getByText("Live",{exact:true}).waitFor();
    check("Delayed old snapshot cannot undo live update",await livePages.reader.locator('tr[data-tracking-id="DEF789"]').getByText("Stockholm",{exact:true}).count()===1);
   }
  }
  let csrf=(await (await sockets.reader.context.request.get(base+"session")).json()).csrf;
  check("Socket owner logout", (await sockets.reader.context.request.post(base+"logout",{headers:{"X-CSRF-Token":csrf},data:""})).status()===204);
  await sockets.reader.page.waitForFunction(()=>window.socketClosed);
  const readerCount=await sockets.reader.page.evaluate(()=>window.framesReceived.length);
  check("Logout closes existing socket",true);
  await livePages.reader.locator("#live-status").getByText("Session ended. Sign in again.",{exact:true}).waitFor();
  check("Logout clears UI cargo data",await livePages.reader.locator("#live-cargos tbody tr").count()===0 && await livePages.reader.locator("#live-markers a").count()===0);
  await trigger(2);
  await sockets.admin.page.waitForFunction(()=>window.framesReceived.length>=2);
  check("No new data after logout",await sockets.reader.page.evaluate(()=>window.framesReceived.length)===readerCount);
  socketObservations["WS-01::Reader::logged_out"]=await revokedSocket(sockets.reader,"logged_out",await sockets.reader.page.evaluate(()=>window.socketClosed),await sockets.reader.page.evaluate(()=>window.framesReceived.length)===readerCount);
  // No HTTP requests refresh the Operator session; socket traffic must not keep it alive.
  for(let i=0;i<5;i++){await sockets.admin.page.waitForTimeout(15000);await trigger(3+i);}
  await sockets.operator.page.waitForFunction(()=>window.socketClosed);
  const expiredCount=await sockets.operator.page.evaluate(()=>window.framesReceived.length);
  check("HTTP idle expiry closes active socket",true);
  await livePages.operator.locator("#live-status").getByText("Session ended. Sign in again.",{exact:true}).waitFor();
  check("Idle expiry clears UI cargo data",await livePages.operator.locator("#live-cargos tbody tr").count()===0 && await livePages.operator.locator("#live-markers a").count()===0);
  await trigger(8);
  await livePages.admin.locator('tr[data-tracking-id="DEF789"]').getByText("New York",{exact:true}).waitFor();
  check("Post-expiry event reaches authorized UI",true);
  check("Revoked UI remains empty",await livePages.reader.locator("#live-cargos tbody tr").count()===0 && await livePages.operator.locator("#live-cargos tbody tr").count()===0);
  check("No new data after idle expiry",await sockets.operator.page.evaluate(()=>window.framesReceived.length)===expiredCount);
  socketObservations["WS-01::Operator::expired"]=await revokedSocket(sockets.operator,"expired",await sockets.operator.page.evaluate(()=>window.socketClosed),await sockets.operator.page.evaluate(()=>window.framesReceived.length)===expiredCount);
  // Each independent observation window starts with a live positive control.
  // Do not reuse a transport that may have closed during the preceding window.
  // KAN-26: retain the original aging transport as a diagnostic subject.
  // The separate fresh witness still controls all access-policy observations.
  await traceSocket("aging-witness-before-second-window",sockets.admin);
  const secondWitnessPage=await sockets.admin.context.newPage();
  await secondWitnessPage.goto(base+"session");
  const secondIdentity=JSON.parse(await secondWitnessPage.textContent("body"));
  check("Second-window witness native identity",secondIdentity.principal==="admin"&&secondIdentity.roles.includes("Administrator"));
  check("Second-window witness preserves original native session",(await saveSocketCookie(sockets.admin))===sockets.admin.savedCookie);
  const secondWitness={...sockets.admin,page:secondWitnessPage,identity:secondIdentity};
  witnessForDiagnostics=secondWitness;
  await secondWitness.page.evaluate(url=>{
   window.framesReceived=[];window.socketClosed=false;window.socketOpenedAt=Date.now();window.socketCloseInfo=null;
   window.liveSocket=new WebSocket(url);window.liveSocket.onmessage=e=>window.framesReceived.push(JSON.parse(e.data));
   window.liveSocket.onclose=e=>{window.socketClosed=true;window.socketCloseInfo={code:e.code,reason:e.reason,at:Date.now()};};
  },base.replace("http:","ws:")+"tracking?connection="+require("crypto").randomUUID());
  await secondWitness.page.waitForFunction(()=>window.liveSocket.readyState===WebSocket.OPEN);
  check("Second-window witness socket opened",true);
  const extraTargets=[];
  for(const [who,state] of [["reader","expired"],["operator","logged_out"],["admin","logged_out"],["admin","expired"]]){
   const actor=await login(who);actor.state=state;actor.savedCookie=await saveSocketCookie(actor);
   await actor.page.evaluate(url=>{
    window.framesReceived=[];window.socketClosed=false;window.socketOpenedAt=Date.now();window.socketCloseInfo=null;window.liveSocket=new WebSocket(url);
    window.liveSocket.onmessage=e=>window.framesReceived.push(JSON.parse(e.data));
    window.liveSocket.onclose=e=>{window.socketClosed=true;window.socketCloseInfo={code:e.code,reason:e.reason,at:Date.now()};};
   },base.replace("http:","ws:")+"tracking?connection="+require("crypto").randomUUID());
   await actor.page.waitForFunction(()=>window.liveSocket.readyState===WebSocket.OPEN);extraTargets.push(actor);
  }
  await trigger(9);
  await secondWitness.page.waitForFunction(()=>window.framesReceived.some(e=>e.trackingId==="DEF789"));
  check("Second-window witness delivered pre-revocation data",true);
  for(const actor of extraTargets){
   await actor.page.waitForFunction(()=>window.framesReceived.some(e=>e.trackingId==="DEF789"));
   check("Lifecycle socket delivered authorized frame "+actor.who+" "+actor.state,true);
   if(actor.state==="logged_out"){
    await traceSocket("before-extra-logout-"+actor.who,secondWitness);
    const token=(await (await actor.context.request.get(base+"session")).json()).csrf;
    check("Lifecycle real logout "+actor.who,(await actor.context.request.post(base+"logout",{headers:{"X-CSRF-Token":token},data:""})).status()===204);
    await actor.page.waitForFunction(()=>window.socketClosed);actor.closedCount=await actor.page.evaluate(()=>window.framesReceived.length);
    await traceSocket("after-extra-logout-"+actor.who,secondWitness);
   }
  }
  // Remaining Reader/Admin sessions receive only WS traffic, never HTTP keepalive.
  for(let index=0;index<5;index++){await secondWitness.page.waitForTimeout(15000);await trigger(10+index);}
  for(const actor of extraTargets){
   await actor.page.waitForFunction(()=>window.socketClosed);
   if(actor.state==="expired")actor.closedCount=await actor.page.evaluate(()=>window.framesReceived.length);
  }
  await secondWitness.page.waitForFunction(()=>window.framesReceived.filter(e=>e.trackingId==="DEF789").length>=6&&window.framesReceived.at(-1).lastKnownLocationCode==="FIHEL");
  check("Second-window witness received last idle-window event",true);
  const witnessCount=await secondWitness.page.evaluate(()=>window.framesReceived.length);
  await trigger(15);await secondWitness.page.waitForFunction(n=>window.liveSocket.readyState===WebSocket.OPEN&&window.framesReceived.length>n&&window.framesReceived.at(-1).lastKnownLocationCode==="SESTO",witnessCount);
  check("Fresh authorized witness receives post-revocation event",true);
  for(const actor of extraTargets){
   const noFrames=await actor.page.evaluate(()=>window.framesReceived.length)===actor.closedCount;
   socketObservations["WS-01::"+roles[actor.who]+"::"+actor.state]=await revokedSocket(actor,actor.state,await actor.page.evaluate(()=>window.socketClosed),noFrames);
  }
  await traceSocket("aging-witness-after-second-window",sockets.admin);
  disconnectEvidence.aging_transport=await sockets.admin.page.evaluate(()=>({openedAt:window.socketOpenedAt,observedAt:Date.now(),readyState:window.liveSocket.readyState,close:window.socketCloseInfo,frameCount:window.framesReceived.length}));
  check("Original transport survives beyond listener timeout",disconnectEvidence.aging_transport.readyState===1&&disconnectEvidence.aging_transport.observedAt-disconnectEvidence.aging_transport.openedAt>90000);
  await sockets.admin.page.waitForFunction(()=>window.framesReceived.filter(e=>e.trackingId==="DEF789").length>=15&&window.framesReceived.at(-1).lastKnownLocationCode==="SESTO");
  check("Original transport receives post-timeout actual cargo",true);
  const freshCargo=cfg.fixture_tracking_id;
  check("Distinct fresh cargo supplied",typeof freshCargo==="string"&&freshCargo!=="DEF789");
  const producer=await (await replayClient.get(base+"session",{headers:{Cookie:sockets.admin.savedCookie}})).json();
  const received=await replayClient.post(base+"rest/handling/reports",{headers:{Cookie:sockets.admin.savedCookie,"X-CSRF-Token":producer.csrf},data:{trackingId:freshCargo,eventType:"RECEIVE",unLocode:"CNHKG",completionTime:"2030-01-01 10:00"}});
  check("Unrelated cargo accepted after peer reset",received.status()===204);
  await secondWitness.page.waitForFunction(id=>window.framesReceived.some(e=>e.trackingId===id&&e.transportStatus==="IN_PORT"&&e.lastKnownLocationCode==="CNHKG"),freshCargo);
  check("Healthy witness receives unrelated cargo after peer reset",true);
  const readback=await login("reader");let persisted=false;
  for(let n=0;n<50&&!persisted;n++){
   const response=await readback.context.request.get(base+"rest/cargo");
   check("Independent Reader readback authorized "+n,response.status()===200);
   persisted=(await response.json()).some(e=>e.trackingId===freshCargo&&e.transportStatus==="IN_PORT"&&e.lastKnownLocationCode==="CNHKG");
   if(!persisted)await readback.page.waitForTimeout(200);
  }
  check("Unrelated cargo persists in independent Reader transaction",persisted);
  disconnectEvidence.unrelated_cargo={tracking_id:freshCargo,http_status:received.status(),healthy_witness_received:true,independent_reader_persistence_verified:persisted};
  await secondWitness.page.evaluate(()=>window.liveSocket.close(1000,"regression complete"));
  await secondWitness.page.waitForFunction(()=>window.socketClosed);
  check("Healthy witness graceful close handshake",await secondWitness.page.evaluate(()=>window.socketCloseInfo.code===1000));
  disconnectEvidence.graceful_close_code=1000;
  check("No page or asset errors",failures.length===0);
 } catch(error){try{await traceSocket("failure",witnessForDiagnostics);}catch(ignored){}checks.push({name:stage+" failed ("+error.name+")",outcome:"FAIL",passed:false});process.exitCode=1;}
 finally{if(abruptPeer&&!abruptPeer.socket.destroyed)abruptPeer.socket.destroy();if(replayClient)await replayClient.dispose();await browser.close();fs.writeFileSync("/out/results.json",JSON.stringify({scope:"Real Chromium cargo read/booking/destination/routing/live/handling workflows",checks,last_navigation:navigation,resource_errors:failures,page_semantics:pageSemantics,socket_observations:socketObservations,socket_diagnostics:socketTrace,disconnect_evidence:disconnectEvidence,navigation_actions:actionProofs,claimed_cargo_actions:claimedCargoProofs},null,2)+"\n");}
})();
