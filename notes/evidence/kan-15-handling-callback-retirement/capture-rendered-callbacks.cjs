const crypto=require("crypto");
const {chromium}=require("playwright");
const path="http://legacy:8080/cargo-tracker/mobile.xhtml";
const actionSpecs=[
 {id:"ACTION-36",source:"firstScreen:firstForm:trackingId",input:"firstScreen:firstForm:trackingId",value:"ABC123"},
 {id:"ACTION-37",source:"firstScreen:firstForm:portCode",input:"firstScreen:firstForm:portCode",value:"USCHI"},
 {id:"ACTION-38",source:"firstScreen:firstForm:eventType",input:"firstScreen:firstForm:eventType",value:"LOAD"},
 {id:"ACTION-39",source:"firstScreen:firstForm:voyage",input:"firstScreen:firstForm:voyage",value:"0100S"}
];
function sanitizeRequest(req,spec){
 const params=new URLSearchParams(req.postData()||"");
 const dynamic=new Set(["javax.faces.ViewState","javax.faces.ClientWindow"]);
 const rows=[...params.entries()].map(([name,value])=>({name,value:dynamic.has(name)?"<present; value redacted>":value}));
 const get=(name)=>params.get(name);
 return {legacy_id:spec.id,method:req.method(),path:new URL(req.url()).pathname,
  content_type:req.headers()["content-type"]||null,faces_request:req.headers()["faces-request"]||null,
  ajax:get("javax.faces.partial.ajax")==="true",source_component_id:get("javax.faces.source"),
  behavior_event:get("javax.faces.behavior.event"),partial_event:get("javax.faces.partial.event"),
  execute:get("javax.faces.partial.execute"),render:get("javax.faces.partial.render"),
  callback_input_name:spec.input,selected_value:params.get(spec.input),parameter_names:rows.map(x=>x.name),
  parameters:rows,viewstate_present:params.has("javax.faces.ViewState"),clientwindow_present:params.has("javax.faces.ClientWindow")};
}
(async()=>{
 const browser=await chromium.launch({headless:true});
 try{
  const page=await (await browser.newContext()).newPage();
  const response=await page.goto(path,{waitUntil:"domcontentloaded",timeout:60000});
  if(!response||response.status()!==200)throw new Error("Legacy flow entry failed with "+(response&&response.status()));
  const html=await response.body(), callbacks=[];
  await page.waitForTimeout(1000);
  for(const spec of actionSpecs){
   const wait=page.waitForRequest(req=>req.method()==="POST"&&new URLSearchParams(req.postData()||"").get("javax.faces.source")===spec.source,{timeout:15000});
   await page.locator('select[name="'+spec.input+'"]').selectOption(spec.value);
   const req=await wait, result=await req.response();
   if(!result||result.status()!==200)throw new Error(spec.id+" callback failed");
   await result.finished();await page.waitForTimeout(800);
   callbacks.push({...sanitizeRequest(req,spec),response_status:result.status()});
  }
  const next=page.locator("#firstScreen\\:nextBtn");
  if(await next.isDisabled())throw new Error("Legacy flow did not enable its second screen after valid selections");
  await next.click();await page.waitForTimeout(500);
  const dateInput="secondScreen:j_idt31:completionDate_input";
  await page.locator("#secondScreen\\:j_idt31\\:completionDate_input").click();
  const today=page.locator(".ui-datepicker-today a");
  await today.waitFor({state:"visible",timeout:10000});
  const dateWait=page.waitForRequest(req=>req.method()==="POST"&&new URLSearchParams(req.postData()||"").get("javax.faces.source")==="secondScreen:j_idt31:completionDate",{timeout:15000});
  await today.click();
  const dateReq=await dateWait,dateResponse=await dateReq.response();
  if(!dateResponse||dateResponse.status()!==200)throw new Error("ACTION-42 callback failed");
  await dateResponse.finished();
  callbacks.push({...sanitizeRequest(dateReq,{id:"ACTION-42",source:"secondScreen:j_idt31:completionDate",input:dateInput}),response_status:dateResponse.status()});
  const capture={task:"KAN-15 source-rendered legacy handling callback capture",capture_date:"2026-11-17",
   legacy_source_revision:"57fc7b32d2597e43b5e0d454e707e0146de5258a",entry_path:"/cargo-tracker/mobile.xhtml",
   rendered_flow_path:new URL(page.url()).pathname.split(";")[0],entry_response_status:response.status(),
   rendered_response_sha256:crypto.createHash("sha256").update(html).digest("hex"),callbacks,
   privacy:{raw_viewstate_retained:false,session_cookie_retained:false,passwords_retained:false},
   capture_method:"Playwright browser-generated request capture; dynamic ViewState and ClientWindow values redacted"};
  console.log(JSON.stringify(capture));
 }finally{await browser.close()}
})().catch(e=>{console.error(e.stack);process.exit(1)});
