(()=>{"use strict";
const base=new URL("../",document.currentScript.src).pathname.replace(/resources\/$/,"");
const status=document.getElementById("live-status"),body=document.querySelector("#live-cargos tbody"),markers=document.getElementById("live-markers");
const places={CNHKG:[22,114],AUMEL:[-38,145],SESTO:[59,18],FIHEL:[60,25],USCHI:[42,-88],JNTKO:[36,140],DEHAM:[54,10],CNSHA:[31,121],NLRTM:[52,5],SEGOT:[58,12],CNHGH:[30,120],USNYC:[41,-74],USDAL:[33,-97]};
const login=document.getElementById("live-login");login.hidden=true;
let generation=0,socket=null,controller=null;const cargos=new Map();const socketVersions=new Map();
function clear(){cargos.clear();socketVersions.clear();body.replaceChildren();markers.replaceChildren();}
function end(message){generation++;if(controller)controller.abort();if(socket){const old=socket;socket=null;old.close();}clear();status.textContent=message;login.hidden=!/sign in/i.test(message);}
function accept(c,fromSocket=false){if(!c||typeof c.trackingId!=="string"||!Number.isFinite(c.updatedAt))return;const old=cargos.get(c.trackingId);const key=c.trackingId+":"+c.updatedAt;
 if(!old||c.updatedAt>old.updatedAt||(c.updatedAt===old.updatedAt&&(fromSocket||socketVersions.get(c.trackingId)!==c.updatedAt))){cargos.set(c.trackingId,c);if(fromSocket)socketVersions.set(c.trackingId,c.updatedAt);}}
function render(){body.replaceChildren();markers.replaceChildren();
 for(const c of [...cargos.values()].sort((a,b)=>a.trackingId.localeCompare(b.trackingId))){
  const row=document.createElement("tr");row.dataset.trackingId=c.trackingId;
  const id=document.createElement("td"),link=document.createElement("a");link.href=base+"admin/show.xhtml?trackingId="+encodeURIComponent(c.trackingId);link.textContent=c.trackingId;id.append(link);row.append(id);
  for(const text of [c.originName,c.destinationName,c.lastKnownLocationName,c.routingStatus,c.transportStatus]){const cell=document.createElement("td");cell.textContent=text;row.append(cell);}body.append(row);
  const code=c.transportStatus==="NOT_RECEIVED"?(c.originCode||c.origin):(c.lastKnownLocationCode||c.lastKnownLocation),point=places[code];
  if(point){const a=document.createElementNS("http://www.w3.org/2000/svg","a");a.setAttribute("href",link.href);a.setAttribute("aria-label",c.trackingId+" at "+code);
   const circle=document.createElementNS(a.namespaceURI,"circle");circle.setAttribute("cx",(point[1]+180)*2);circle.setAttribute("cy",(90-point[0])*2);circle.setAttribute("r","6");circle.setAttribute("fill",c.misdirected?"#b42318":"#174ea6");
   const title=document.createElementNS(a.namespaceURI,"title");title.textContent=c.trackingId+" — "+code;circle.append(title);a.append(circle);markers.append(a);}
 }}
function connect(){end("Connecting…");const current=generation;const aborter=new AbortController();controller=aborter;
 const url=new URL(base+"tracking",location.origin);url.protocol=location.protocol==="https:"?"wss:":"ws:";const bytes=crypto.getRandomValues(new Uint8Array(16));bytes[6]=(bytes[6]&15)|64;bytes[8]=(bytes[8]&63)|128;const hex=[...bytes].map(b=>b.toString(16).padStart(2,"0")).join("");url.searchParams.set("connection",hex.slice(0,8)+"-"+hex.slice(8,12)+"-"+hex.slice(12,16)+"-"+hex.slice(16,20)+"-"+hex.slice(20));
 const ws=new WebSocket(url);socket=ws;
 ws.onopen=async()=>{if(current!==generation)return;try{const response=await fetch(base+"rest/cargo",{credentials:"same-origin",cache:"no-store",signal:aborter.signal});
  if(current!==generation)return;
  if(!response.ok){end(response.status===401||response.status===403?"Session ended. Sign in again.":"Tracking unavailable. Reconnect to retry.");return;}
  const data=await response.json();if(current!==generation||ws.readyState!==WebSocket.OPEN)return;
  for(const c of data)accept(c);render();status.textContent="Live";
 }catch(error){if(current===generation)end("Tracking unavailable. Reconnect to retry.");}};
 ws.onmessage=event=>{if(current!==generation)return;try{accept(JSON.parse(event.data),true);render();}catch(invalid){end("Tracking unavailable. Reconnect to retry.");}};
 ws.onclose=event=>{if(current===generation)end(event.code===1008?"Session ended. Sign in again.":"Disconnected. Reconnect to retry.");};
 ws.onerror=()=>{if(current===generation)end("Connection unavailable. Sign in again or reconnect.");};
}
document.getElementById("live-reconnect").addEventListener("click",connect);window.addEventListener("pagehide",()=>end("Disconnected."));connect();
})();
