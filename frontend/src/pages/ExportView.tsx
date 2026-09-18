import {useState} from "react";import {request} from "../lib/api";
export function ExportView(){const [hash,setHash]=useState("");return <section><h2>6. Export and replay</h2><button onClick={async()=>{const p=await request("/claims/DEMO-001/export",{method:"POST"});setHash(p.fingerprint_sha256);const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([JSON.stringify(p,null,2)],{type:"application/json"}));a.download="claimpilot-package.json";a.click();}}>Export package</button>{hash&&<p>SHA-256 fingerprint: <code>{hash}</code></p>}</section>}

