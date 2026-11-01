const {chromium}=require("playwright");
const fs=require("fs");
const cfg=JSON.parse(fs.readFileSync("/run/credentials.json","utf8"));
const base=cfg.base;
const checks=[];const failures=[];let stage="initialize";let navigation=null;
function check(name,ok){stage=name;checks.push({name,passed:!!ok});if(!ok)throw new Error(name);}
(async()=>{
 const browser=await chromium.launch({headless:true});
 try {
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
   check("Browser login "+who,(await page.textContent("body")).includes('"principal":"'+who+'"'));
   return {context,page};
  }
  const reader=await login("reader");
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
  const operator=await login("operator");
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
  const admin=await login("admin");await book(admin);
  await operator.page.goto(base+"admin/book.xhtml");
  await operator.page.getByLabel("Origin",{exact:true}).selectOption("CNHKG");
  await operator.page.getByLabel("Destination",{exact:true}).selectOption("FIHEL");
  await operator.page.getByLabel("Arrival deadline (YYYY-MM-DD)").fill("2000-01-01");
  await operator.page.getByRole("button",{name:"Book cargo",exact:true}).click();
  await operator.page.waitForURL(/admin\/show.xhtml\?trackingId=/);
  await operator.page.getByRole("link",{name:"Assign route",exact:true}).click();
  await operator.page.getByText("No sample routes meet this cargo's arrival deadline.",{exact:true}).waitFor();
  check("No candidates for expired deadline handled",await operator.page.getByRole("button",{name:"Assign selected route",exact:true}).count()===0);
  // Mobile viewport verifies this responsive increment; old mobile event logger remains disabled.
  await operator.page.setViewportSize({width:390,height:844});
  await operator.page.goto(base+"admin/show.xhtml?trackingId="+id);
  check("Cargo details fit mobile viewport",await operator.page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));
  const malicious=await ap.request.get(base+"jakarta.faces.resource/core.js.xhtml?ln=primefaces&pfdrid=forged");
  check("Dynamic resource bypass denied",malicious.status()===404);
  const wsHeaders={"Upgrade":"websocket","Connection":"Upgrade","Sec-WebSocket-Version":"13","Sec-WebSocket-Key":Buffer.from("0123456789abcdef").toString("base64"),"Origin":new URL(base).origin};
  let denied=await ap.request.get(base+"tracking?connection="+require("crypto").randomUUID(),{headers:wsHeaders});
  check("Anonymous upgrade is HTTP401",denied.status()===401);
  const sockets={};const livePages={};
  let snapshotReadyResolve,releaseSnapshot;
  const snapshotReady=new Promise(resolve=>snapshotReadyResolve=resolve);
  const snapshotRelease=new Promise(resolve=>releaseSnapshot=resolve);
  for(const who of ["reader","operator","admin"]){
   sockets[who]=await login(who);
   const bad=await sockets[who].context.request.get(base+"tracking?connection="+require("crypto").randomUUID(),{headers:{...wsHeaders,Origin:"https://untrusted.example"}});
   check("Authenticated wrong-origin upgrade denied "+who,bad.status()===403);
   await sockets[who].page.evaluate(url=>{
    window.framesReceived=[];window.socketClosed=false;
    window.liveSocket=new WebSocket(url);
    window.liveSocket.onmessage=e=>window.framesReceived.push(JSON.parse(e.data));
    window.liveSocket.onclose=()=>window.socketClosed=true;
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
   const csrf=(await (await sockets.admin.context.request.get(base+"session")).json()).csrf;
   const response=await sockets.admin.context.request.post(base+"rest/handling/reports",{headers:{"X-CSRF-Token":csrf},data:{trackingId:"DEF789",eventType:"CUSTOMS",unLocode:sequence===8?"USNYC":sequence%2===1?"SESTO":"FIHEL",completionTime:"2031-01-"+String(sequence).padStart(2,"0")+" 10:00"}});
   check("Actual handling trigger "+sequence,response.status()===204);
  }
  await trigger(1);
  for(const who of ["reader","operator","admin"]){
   await sockets[who].page.waitForFunction(()=>window.framesReceived.some(e=>e.trackingId==="DEF789"));
   check("Actual authorized data frame "+who,true);
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
  check("No page or asset errors",failures.length===0);
 } catch(error){checks.push({name:stage+" failed ("+error.name+")",outcome:"FAIL",passed:false});process.exitCode=1;}
 finally{await browser.close();fs.writeFileSync("/out/results.json",JSON.stringify({scope:"Real Chromium Faces cargo read/booking/destination/routing workflows; not full KAN-19",checks,last_navigation:navigation,resource_errors:failures},null,2)+"\n");}
})();
