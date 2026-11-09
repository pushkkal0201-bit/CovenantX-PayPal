# Run and test CovenantX locally

Use Python 3.12 and Node.js 22 or later. Run the backend from the repository root and the frontend from `apps/web`. Keep both terminals open while you use the app.

## Start the backend

In Windows Command Prompt:

```bat
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe scripts\configure_local.py
.venv\Scripts\python.exe scripts\run_api.py
```

On macOS or Linux, activate the environment with `source .venv/bin/activate` and run the same scripts with `python`. If you already have a working virtual environment, reuse it. If `.env` exists, skip `configure_local.py` and edit the existing file. The script generates separate client and vendor tokens and a database password.

## Start the web app

In a second terminal:

```bash
cd apps/web
npm ci
npm run dev
```

Open [CovenantX](http://localhost:3000). Copy the value of `CLIENT_TOKEN` or `VENDOR_TOKEN` from `.env` into **Workspace access token**. To switch roles, use **Lock workspace** or reload the page and unlock with the other token. Saved milestones remain in the database.

## Configure Gemini and PayPal Sandbox

Use `KEY=value` lines in the project root's `.env`. Keep credentials and role tokens local.

| Setting | Value |
| --- | --- |
| `GEMINI_API_KEY` | Your Google AI Studio API key |
| `GEMINI_MODEL` | The exact model ID available to your API key |
| `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET` | Credentials from the same PayPal Sandbox merchant app |
| `PUBLIC_WEB_URL` | Browser origin and PayPal return destination. The local default is `http://localhost:3000`. |
| `PAYPAL_WEBHOOK_ID` | ID of a registered Sandbox webhook. Leave blank for manual capture and reconciliation. |
| `DATABASE_URL` | Use the generated SQLite setting for local testing. |

In Windows Command Prompt, run the following from the repository root:

```bat
.venv\Scripts\python.exe scripts\preflight.py --mode sandbox
```

Fix any failed check, then restart the backend to load the settings. Existing environment variables take precedence over `.env`. Add `--webhook` to preflight when testing webhook delivery. Preflight and [API health](http://127.0.0.1:8000/api/health) check that settings are present. The first actual review and checkout calls exercise model access and PayPal authentication.

## Test Gemini and PayPal Sandbox

Use the committed `README.md` as evidence for a documentation delivery. From the repository root, run `git rev-parse HEAD` to get the commit SHA. Use the unmodified README from that commit.

1. **Client:** In **Contract & evidence**, create a milestone named `Documentation delivery - Sandbox test` for `10.00` USD using that SHA. In **Original agreed terms**, enter `USD 10 for delivery of README.md at the specified commit. Deduct USD 2 if the document is missing.`
2. Keep one clause. Use ID `DOC-01`, measurement **Document presence (0 / 1)**, criterion `README.md is present in the delivered commit.`, comparison **At least**, threshold `1` and deduction `2.00`. Click **Create draft** and **Approve active contract**.
3. **Vendor:** Unlock with the vendor token and select the new milestone. Under **Import delivery reports**, choose `README.md` in **Delivery documentation**. Enter the same commit SHA, use `readme-delivery-01` as the artifact reference and enter the commit-specific GitHub URL for the README as the source. Keep the prefilled observation time if you are inspecting the file now. Clear **Demonstration data** for this delivery and click **Parse and submit reports**.
4. **Client:** Unlock with the client token. Compare the uploaded document with the file at the recorded commit, record what you checked in **Client inspection note**, and click **Attest active evidence**. Open **Verification** and click **Run Gemini review**. Review the citation and resolve any hold before proceeding.
5. In **Settlement studio**, check that the proposal is `10.00` USD with no deductions and click **Approve settlement snapshot**. In **PayPal operations**, click **Create sandbox order** and **Approve on PayPal**. Use your PayPal Sandbox Personal buyer account to approve the order.
6. Return to CovenantX and click **Capture approved order**, then **Reconcile provider**. Check for `COMPLETED` and a recorded capture ID. Export the record from **Evidence passport** if you want to retain it.

If a capture response is uncertain, reconcile the existing order before taking another payment action. If the provider outcome remains unclear, inspect that order in Sandbox.

## Troubleshoot startup

- **Port 8000 is already in use.** Open the health endpoint first. If CovenantX is already running with the expected settings, keep it running. To reload settings, stop the original API with **Ctrl+C** in its terminal and restart it.
- **The workspace shows provider settings as missing.** Check the API directly, then open [the same health endpoint through the web app](http://localhost:3000/api/health). If the API reports the expected settings but the web endpoint fails, check that the Next.js proxy points to the running API.
- **npm reports no space on Windows.** In the web terminal, use a writable folder on a drive with space for `TEMP`, `TMP` and `npm_config_cache`. Run `npm config get cache` to confirm the cache path before retrying `npm ci`.
