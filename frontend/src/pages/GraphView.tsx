import {EvidenceGraph} from "../components/EvidenceGraph"; import type {GraphData} from "../lib/schemas";
export function GraphView({data,onCorrect}:{data:GraphData|null,onCorrect:()=>void}){return <section><h2>4. Replayable evidence graph</h2><button onClick={onCorrect}>Upload scripted corrected bill</button>{data&&<><p>{data.corrected?"After correction — changed nodes are highlighted":"Before correction"}</p><EvidenceGraph data={data}/></>}</section>}

