import { z } from "zod";
export const State = z.enum(["VERIFIED","UNVERIFIED","CONFLICTED","MISSING","NEEDS_HUMAN_CONFIRMATION"]);
export const Graph = z.object({claim_id:z.string(),corrected:z.boolean(),nodes:z.array(z.object({id:z.string(),content:z.string(),state:State,value:z.unknown(),changed:z.boolean(),metadata:z.record(z.string(),z.unknown())})),edges:z.array(z.object({from:z.string(),to:z.string(),edge_type:z.string(),rule_id:z.string().nullable()}))});
export type GraphData = z.infer<typeof Graph>;

