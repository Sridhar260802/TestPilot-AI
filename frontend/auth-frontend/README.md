# Auth Frontend — Ready to Run

This is a complete, standalone project. Nothing to merge or copy — just
install and run.

## Run it

Open this folder in VS Code, open a terminal (`` Ctrl + ` ``), and run:

```bash
npm install
npm run dev
```

Then open the URL it prints (usually `http://localhost:5173`). It will
redirect straight to `/login`.

## Google Sign-In (optional for now)

The "Continue with Google" button will show a small notice until you set
this up — everything else (email/password login, signup, forgot password)
works without it.

1. Copy `.env.example` to `.env`.
2. Get a Client ID from the
   [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
   (OAuth client ID → Web application → add `http://localhost:5173` as an
   authorized origin).
3. Put it in `.env`:
   ```
   VITE_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   ```
4. Restart `npm run dev`.

## What's connected to a backend, and what isn't

Login, signup, and Google sign-in all call a Python backend that **doesn't
exist yet** (`/api/auth/login`, `/api/auth/signup`, `/api/auth/google`) — so
right now, submitting the forms will show a real "could not reach the
server" error. That's expected; nothing is faked. See `src/services/authService.js`
for the exact endpoints and response shapes the backend needs to implement.

## Where things live

```
src/
├── App.jsx, main.jsx, index.css   ← app entry + routing setup
├── components/auth/                ← LoginForm, SignupForm, GoogleSignInButton, etc.
├── pages/                            ← Login.jsx, Signup.jsx, ForgotPassword.jsx
├── services/                          ← authService.js (backend calls), googleAuth.js
├── routes/authRoutes.jsx              ← /login, /signup, /forgot-password
├── hooks/useAuth.js                   ← optional, for reading auth state elsewhere
└── utils/validation.js                ← email/password validation rules
```

## If you want to merge this into an existing project instead

Copy everything inside `src/` (except don't overwrite an `App.css` you
already have content in) into your existing project's `src/` folder, and
copy `tailwind.config.js` / `postcss.config.js` to its root if it doesn't
already have Tailwind set up. Then `npm install react-router-dom` there.
