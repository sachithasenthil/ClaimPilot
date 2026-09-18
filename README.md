# ClaimPilot hackathon prototype

ClaimPilot is a claimant-held, strictly non-predictive health-insurance evidence demo. It exposes uncertainty as five explicit states, runs one fixed correction cascade, and exports a package whose SHA-256 state digest can be replayed without database access.

## Run the backend

Requires Python 3.11+.

```powershell
cd C:\Users\LENOVO\ClaimPilot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
# Edit backend\.env and replace the placeholder with your Gemini API key.
$env:PYTHONPATH="C:\Users\LENOVO\ClaimPilot\backend"
python -m uvicorn app.main:app --reload
```

The Gemini key is needed only for candidate-rule generation. API docs are at `http://localhost:8000/docs`.

## Run the frontend

In a second terminal:

```powershell
cd C:\Users\LENOVO\ClaimPilot\frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Vite proxies `/api` to the backend.

## Demo sequence

1. The seeded Section 5 before-state is available at `GET /claims/DEMO-001/graph`.
2. Upload a policy PDF, generate a candidate with Gemini, and select **Verify** or **Reject** in the split review.
3. Select **Upload scripted corrected bill**. The fixed traversal changes stay from 4 to 3 days, eligible room rent from Rs 20,000 to Rs 15,000, flags the boundary, matches the MRI report, and creates C1.
4. The non-correctable-condition panel plainly stops with no action available.
5. Select **Export package** to download `claimpilot-package.json`.

## Replay an export without the database

```powershell
cd C:\Users\LENOVO\ClaimPilot\backend
python replay_validator.py C:\path\to\claimpilot-package.json
```

The validator prints `MATCH` when both the package fingerprint and recomputed state digest agree.

## Tests

```powershell
cd C:\Users\LENOVO\ClaimPilot
$env:PYTHONPATH="backend"
python -m pytest backend\tests -q
```

Tests cover uncertainty propagation, the exact cascade, and schema-level rejection of predictive or guaranteed language.
