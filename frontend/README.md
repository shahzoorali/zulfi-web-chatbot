# Chat Frontend (Vercel-ready)

## Configure
1. Copy `.env.example` to `.env` and set:
   - `VITE_API_BASE` = your FastAPI base (e.g., https://api.example.com)
   - `VITE_API_KEY`  = optional X-API-Key (if backend enforces it)
   - `VITE_DEFAULT_RUN_ID` = optional run id to scope answers

## Local dev
```bash
cd frontend
npm i
npm run dev
```

## Build
```bash
npm run build && npm run preview
```

## Deploy to Vercel
- Import this `frontend` folder as a project
- Build command: `npm run build`
- Output directory: `dist`
- Environment variables: same as `.env`

## Standalone chat page
- After deploy, open: `https://<your-vercel-app>.vercel.app/`

## Embed on any website
Add this before `</body>`:
```html
<script src="https://<your-vercel-app>.vercel.app/embed.js"
        data-api-base="https://api.example.com"
        data-api-key=""
        data-run-id=""
        data-title="Chat with us"
        data-color="#1452cc"></script>
```

- `data-api-base`: your FastAPI host (must expose POST /answer, CORS enabled)
- `data-api-key`: optional key if required by backend
- `data-run-id`: optional run id to constrain search
- `data-title`/`data-color`: branding 