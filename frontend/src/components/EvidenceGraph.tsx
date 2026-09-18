import type { GraphData } from "../lib/schemas";
const colors:Record<string,string>={VERIFIED:"#16815c",UNVERIFIED:"#64748b",CONFLICTED:"#dc2626",MISSING:"#d97706",NEEDS_HUMAN_CONFIRMATION:"#7c3aed"};
export function EvidenceGraph({data}:{data:GraphData}){return <div className="graph" aria-label="Evidence dependency graph">{data.nodes.map((n,i)=><div key={n.id} className={`node ${n.changed?"changed":""}`} style={{borderColor:colors[n.state],left:`${(i%4)*24+2}%`,top:`${Math.floor(i/4)*150+20}px`}}><strong>{n.id}</strong><span>{n.content}</span><em style={{color:colors[n.state]}}>{n.state.replaceAll("_"," ")}</em><code>{JSON.stringify(n.value)}</code>{n.metadata.boundary_sensitive===true&&<b>Boundary sensitive</b>}</div>)}</div>}

