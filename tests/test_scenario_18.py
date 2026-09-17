from claimpilot.engine.crg import ClaimResolutionGraph
from claimpilot.engine.resolver import resolve_ownership
from claimpilot.models.enums import IssueClass, NodeKind, UncertaintyState as S
from claimpilot.models.graph import EvidenceEdge, EvidenceNode, Issue

def test_section_18_multibranch_propagation():
    g=ClaimResolutionGraph()
    def node(id, state=S.VERIFIED, value=None, **metadata): g.add_node(EvidenceNode(id=id,kind=NodeKind.EVIDENCE,state=state,value=value,metadata=metadata))
    node("R1",value=5000); node("R2",value=30); node("R3"); node("final_admission",value="03-Mar"); node("discharge",value="07-Mar"); node("summary_admission",value="03-Mar"); node("E2",value="02-Feb"); node("E3",state=S.MISSING); node("D1",state=S.UNVERIFIED,value="04-Mar MRI"); node("I1",state=S.MISSING)
    node("stay",state=S.UNVERIFIED); node("room",state=S.UNVERIFIED); node("prewindow",state=S.UNVERIFIED)
    for src,tgt in [("final_admission","stay"),("discharge","stay"),("stay","room"),("R1","room"),("final_admission","prewindow"),("R2","prewindow")]: g.add_edge(EvidenceEdge(source_id=src,target_id=tgt))
    g._computations["stay"] = lambda ns,n: n.model_copy(update={"state":S.VERIFIED,"value": 3 if ns["final_admission"].value=="04-Mar" else 4})
    g._computations["room"] = lambda ns,n: n.model_copy(update={"state":S.VERIFIED,"value":ns["stay"].value*ns["R1"].value})
    g._computations["prewindow"] = lambda ns,n: n.model_copy(update={"state":S.VERIFIED,"value":"02-Feb" if ns["final_admission"].value=="04-Mar" else "01-Feb"})
    g.recompute(); assert (g.nodes["stay"].value,g.nodes["room"].value)==(4,20000)
    # Corrected final bill: all dependent branches recompute.
    g.replace_node(g.nodes["final_admission"].model_copy(update={"value":"04-Mar"})); g.replace_node(g.nodes["E3"].model_copy(update={"state":S.VERIFIED,"value":"MRI 04-Mar code"})); g.replace_node(g.nodes["D1"].model_copy(update={"state":S.VERIFIED})); g.replace_node(g.nodes["I1"].model_copy(update={"state":S.VERIFIED}))
    g.recompute()
    assert g.nodes["stay"].value == 3 and g.nodes["room"].value == 15000
    assert g.nodes["prewindow"].value == "02-Feb" and g.nodes["E2"].metadata.get("boundary_sensitive") is None
    # Boundary flag is evidence metadata and remains verified.
    g.replace_node(g.nodes["E2"].model_copy(update={"metadata":{"boundary_sensitive":True}})); assert g.nodes["E2"].state == S.VERIFIED
    assert g.nodes["I1"].state == S.VERIFIED
    g.add_node(EvidenceNode(id="C1",kind=NodeKind.ISSUE,state=S.CONFLICTED,value="Final Bill disagrees with Discharge Summary"))
    conflict=Issue(id="C1",issue_class=IssueClass.CONFLICT,description="Final Bill disagrees with Discharge Summary",authoritative_issuer="Hospital")
    assert g.nodes["C1"].state == S.CONFLICTED
    ownership=resolve_ownership(conflict); assert (ownership.evidence_owner,ownership.resolution_owner)==("Hospital","Claimant")
