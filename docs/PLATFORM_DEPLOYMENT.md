# NepSense Unified Platform Deployment (Low-Cost, Stable)

This document defines a production deployment for one clean domain that serves landing, dashboard, billing, docs, and API.

## Target Product Surface

- `/` landing and portfolio-led product page
- `/pricing` API credit packs (Rs. 50 / Rs. 100 / Rs. 500)
- `/docs` quick docs page, with interactive API docs at `/api/docs`
- `/dashboard` account and usage
- `/dashboard/billing` payment + credit history
- `/dashboard/api-keys` key management
- `/data` data coverage + downloads
- `/status` API and data/admin status
- `/api/v1/...` programmatic API

## Cheapest Stable Architecture

1. Cloud Run service (`nepsense-api`) hosts both API and built frontend.
2. Cloud Build builds a single container image from the repository root.
3. Domain mapping points product domain directly to this Cloud Run service.
4. SQLite can be used for early stage, but migrate to Cloud SQL Postgres for multi-instance durability.
5. Keep GitHub repository as public data mirror for trust/transparency.

## Payments

1. Khalti as primary checkout route (`/api/v1/payments/khalti/*`).
2. eSewa as secondary fallback route (`/api/v1/payments/esewa/*`).
3. Credit-pack model only (no monthly subscription required).
4. Credit usage is deducted per endpoint through API key middleware.

## Environment Variables

Set these in Cloud Run:

- `APP_BASE_URL=https://<your-domain>`
- `FRONTEND_URL=https://<your-domain>`
- `KHALTI_SECRET_KEY=...`
- `KHALTI_PUBLIC_KEY=...`
- `ESEWA_MERCHANT_CODE=...`
- `ESEWA_SECRET_KEY=...`
- `NEPSENSE_BILLING_DB=/var/lib/nepsense/billing.sqlite3` (or move to Cloud SQL)

## Deploy

Use existing `cloudbuild.yaml` from repo root:

```bash
gcloud builds submit --config cloudbuild.yaml
```

## Immediate Next Production Upgrades

1. Add JWT auth for dashboard routes and enforce user ownership checks on billing/api-key endpoints.
2. Move billing persistence from SQLite to Cloud SQL Postgres before scaling above one instance.
3. Add webhook/event audit table for payment reconciliation.
4. Add monthly usage exports and invoice PDFs.
5. Add admin-only route protection and role-based access.
