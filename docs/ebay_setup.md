# eBay OAuth setup (Application access token)

This guide covers obtaining eBay API keys for FretScout and configuring local
OAuth credentials. This step only establishes OAuth for later ingestion work.

## 1) Create an eBay Developer Program account

1. Visit https://developer.ebay.com/
2. Sign in or create an account.
3. Enroll in the eBay Developer Program.

## 2) Create an application (keyset)

1. In the developer portal, create an Application/keyset.
2. Copy the following values:
   - **Client ID** (App ID)
   - **Client Secret** (Cert ID)

Note: eBay issues separate keysets for **Sandbox** and **Production**. Use the
matching keyset for the environment you intend to test against.

## 3) Configure environment variables locally

```bash
export EBAY_CLIENT_ID="your-client-id"
export EBAY_CLIENT_SECRET="your-client-secret"
export EBAY_ENV="production"
```

Set `EBAY_ENV` to `sandbox` if you want to use the sandbox token endpoint.

## 4) Run the manual OAuth smoke test

```bash
python scripts/ebay_oauth_smoke.py
```

This prints a success message and an approximate `expires_in` value without
printing the raw access token.
