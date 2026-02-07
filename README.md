# FretScout (MVP)

Used & vintage guitar discovery with deal valuation and alerts (click-out, no transactions).

## Goal
Search used/vintage listings across sources, score relative value, and notify users when great matches appear.

## Status
In development.

## Run
1. Install dependencies: `pip install -r requirements.txt`
2. Start the app: `streamlit run app.py`

## CI / Smoke Test
Run the smoke test script locally:

```
python scripts/smoke_test.py
```

## Project structure
```
.
├── app.py
├── fretscout
│   ├── alerts.py
│   ├── connectors
│   │   └── stub.py
│   ├── db.py
│   ├── models.py
│   └── valuation.py
├── README.md
└── requirements.txt
```
