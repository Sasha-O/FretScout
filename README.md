# FretScout (MVP)

Used & vintage guitar discovery with deal valuation and alerts (click-out, no transactions).

## Goal
Search used/vintage listings across sources, score relative value, and notify users when great matches appear.

## Status
In development.

## Run (local)
1. Create a virtualenv: `python -m venv .venv`
2. Activate it: `source .venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Start the app: `streamlit run app.py`

## Deployment (Streamlit Community Cloud)
1. Push this repo to a public GitHub repository.
2. In Streamlit Community Cloud, choose **Deploy** → select your repo/branch → set the main file to `app.py`.
3. Your app will be available at `https://<appname>.streamlit.app`.

### Secrets (optional, enables live eBay results)
Add the following secrets in **Streamlit Cloud → App → Settings → Secrets**:

```
EBAY_CLIENT_ID="..."
EBAY_CLIENT_SECRET="..."
EBAY_ENV="production"
EBAY_MARKETPLACE_ID="EBAY_US"
```

The app runs without these values in demo mode, but live eBay results require them.

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
