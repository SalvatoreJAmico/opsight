# Opsight Frontend

This package contains the React and Vite frontend for Opsight.

## Local Development

Install dependencies and start the dev server:

```bash
npm install
npm run dev
```

By default, local development uses the Vite proxy routes defined in `vite.config.js`.

Frontend environment examples live in [modules/frontend/.env.example](./.env.example).

## Production Build

Create a production bundle with:

```bash
npm run build
```

Production builds should point to the deployed backend using frontend environment variables such as `VITE_CLOUD_API_URL` or `VITE_API_BASE_URL`.

## Deployment

The frontend is intended to deploy to Azure Static Web Apps through [deploy-frontend.yml](../../.github/workflows/deploy-frontend.yml).

That workflow expects:

- GitHub secret `AZURE_STATIC_WEB_APPS_API_TOKEN`
- GitHub repository variables for frontend build-time URLs such as `VITE_CLOUD_API_URL`

If the deployed frontend and API run on different origins, configure the backend `CORS_ALLOWED_ORIGINS` value to include the frontend URL.
