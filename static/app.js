function fmtBytes(n){
  if(n < 1024**2) return (n/1024).toFixed(0)+" KB";
  if(n < 1024**3) return (n/1024**2).toFixed(0)+" MB";
  return (n/1024**3).toFixed(1)+" GB";
}
function uptime(sec){
  sec=Math.floor(Number(sec));
  const d=Math.floor(sec/86400); sec%=86400;
  const h=Math.floor(sec/3600); sec%=3600;
  const m=Math.floor(sec/60);
  return `${d}d ${h}h ${m}m`;
}
async function refresh(){
  try{
    const r=await fetch("/api/status",{cache:"no-store"});
    const d=await r.json();
    document.getElementById("clock").textContent=d.time;
    document.getElementById("cpu").textContent=d.cpu+"%";
    document.getElementById("cpuBar").style.width=d.cpu+"%";
    document.getElementById("load").textContent="Load "+d.load.join(" / ");
    document.getElementById("ram").textContent=d.ram.percent+"%";
    document.getElementById("ramBar").style.width=d.ram.percent+"%";
    document.getElementById("ramDetail").textContent=fmtBytes(d.ram.used)+" / "+fmtBytes(d.ram.total);
    document.getElementById("temp").textContent=d.temperature===null?"--":d.temperature+"°C";
    document.getElementById("thermal").textContent=d.thermal_zones.map(x=>x.name+" "+x.temp+"°C").join(" · ") || "thermal zone unavailable";
    document.getElementById("disk").textContent=d.disk.percent+"%";
    document.getElementById("diskBar").style.width=d.disk.percent+"%";
    document.getElementById("diskDetail").textContent=fmtBytes(d.disk.used)+" / "+fmtBytes(d.disk.total);
    document.getElementById("queue").textContent=d.dirs.incoming;
    document.getElementById("output").textContent=d.dirs.output;
    document.getElementById("error").textContent=d.dirs.error;
    const a=document.getElementById("activity");
    a.innerHTML=d.activity.length ? d.activity.map(x=>`<div>${escapeHtml(x)}</div>`).join("") : '<div class="empty">No activity yet.</div>';
  }catch(e){
    document.getElementById("clock").textContent="OFFLINE";
  }
}
function escapeHtml(s){return s.replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
async function restartWorker(){
  if(!confirm("Worker를 재시작하시겠습니까?")) return;
  const r=await fetch("/api/worker/restart",{method:"POST",headers:{"X-Dashboard-Action":"cubie"}});
  const d=await r.json();
  alert(d.ok?"Worker restarted.":d.error);
}
async function rebootServer(){
  if(!confirm("서버를 재부팅하시겠습니까?")) return;
  const r=await fetch("/api/system/reboot",{method:"POST",headers:{"X-Dashboard-Action":"cubie"}});
  const d=await r.json();
  if(d.ok) alert("Server rebooting.");
  else alert(d.error);
}
const fileInput=document.getElementById("fileInput");
const dropzone=document.getElementById("dropzone");
const selected=document.getElementById("selectedFiles");
const uploadForm=document.getElementById("uploadForm");
const uploadStatus=document.getElementById("uploadStatus");

function showSelected(){
  const fs=[...fileInput.files];
  selected.textContent=fs.length ? fs.map(f=>`${f.name} (${fmtBytes(f.size)})`).join(" · ") : "";
}
fileInput.addEventListener("change",showSelected);
["dragenter","dragover"].forEach(ev=>dropzone.addEventListener(ev,e=>{
  e.preventDefault(); dropzone.classList.add("drag");
}));
["dragleave","drop"].forEach(ev=>dropzone.addEventListener(ev,e=>{
  e.preventDefault(); dropzone.classList.remove("drag");
}));
dropzone.addEventListener("drop",e=>{
  if(e.dataTransfer.files.length){
    fileInput.files=e.dataTransfer.files;
    showSelected();
  }
});
uploadForm.addEventListener("submit",async e=>{
  e.preventDefault();
  if(!fileInput.files.length){ uploadStatus.textContent="Select a file first."; return; }
  const fd=new FormData();
  [...fileInput.files].forEach(f=>fd.append("files",f));
  uploadStatus.textContent="Uploading...";
  try{
    const r=await fetch("/api/upload",{method:"POST",body:fd});
    const d=await r.json();
    uploadStatus.textContent=d.uploaded?.length
      ? `${d.uploaded.length} file(s) added to queue.` + (d.errors?.length ? ` ${d.errors.length} rejected.` : "")
      : (d.error || "Upload failed.");
    if(d.uploaded?.length){
      fileInput.value="";
      selected.textContent="";
      refresh();
    }
  }catch(err){
    uploadStatus.textContent="Upload failed: "+err;
  }
});

refresh();
setInterval(refresh,3000);
