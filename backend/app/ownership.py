OWNERSHIP = {
    "missing_document_that_exists": {
        "authority": "Hospital / lab", "action_type": "Claimant initiates", "resolution_owner": "Claimant",
        "explanation": "Request the existing document from its issuer.",
    },
    "incorrect_issued_document": {
        "authority": "Hospital", "action_type": "Claimant initiates; hospital executes", "resolution_owner": "Claimant / Hospital",
        "explanation": "Ask the hospital to issue a corrected document.",
    },
    "conflict_between_two_documents": {
        "authority": "Whichever issuer is wrong", "action_type": "Request correction", "resolution_owner": "Claimant",
        "explanation": "The claimant asks the incorrect issuer to correct its document.",
    },
    "policy_ambiguity": {
        "authority": "Insurer / TPA", "action_type": "Seek clarification", "resolution_owner": "Claimant",
        "explanation": "Informational only until the insurer or TPA answers.",
    },
    "non_correctable_policy_condition": {
        "authority": "None", "action_type": "No action exists", "resolution_owner": "Nobody",
        "explanation": "This policy condition cannot be corrected. No action is available; stop here.",
    },
}


def resolution_for(issue_class: str) -> dict[str, str]:
    if issue_class not in OWNERSHIP:
        raise ValueError(f"Unknown issue class: {issue_class}")
    return OWNERSHIP[issue_class].copy()

