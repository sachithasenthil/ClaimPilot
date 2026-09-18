import { Graph, GraphData } from "./schemas";
const request = async (url:string, init?:RequestInit) => { const r=await fetch(`/api${url}`,init); if(!r.ok) throw new Error(await r.text()); return r.json(); };
export async function graph():Promise<GraphData>{return Graph.parse(await request("/claims/DEMO-001/graph"));}
export async function correct():Promise<GraphData>{return Graph.parse(await request("/claims/DEMO-001/documents/final-bill/correct",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({admission_date:"04-Mar",mri_itemized:true,procedure_code:"MRI-BRAIN",procedure_date:"04-Mar"})}));}
export { request };

