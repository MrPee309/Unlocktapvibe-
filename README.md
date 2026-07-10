# UnlockTap — Apple IMEI & Serial Number Checker

A premium, production-ready Apple device verification web app built with **Next.js (App Router)**, **JavaScript**, **Tailwind CSS**, **shadcn/ui** and **MongoDB**. It offers instant IMEI and Apple serial number lookups with a free preview and a credit-based premium report system.

> This build uses a **realistic mock verification engine** and a **mock payment system** so the full flow works out of the box with no external API keys. Secure placeholders are included to plug in real providers later.

## Features

- **Apple IMEI Checker** — validate 15-digit IMEI, free preview + credit-locked premium report (iCloud/Activation Lock, blacklist, warranty, carrier, SIM-lock, etc.).
- **Apple Serial Checker** — validate Apple serial numbers, warranty & coverage lookup.
- **Authentication** — Register, Login, Forgot/Reset Password, Profile (local credentials, hashed passwords + signed HMAC tokens).
- **Credit system** — Single Check, Starter, Technician, Business plans with a mock checkout.
- **User Dashboard** — credits, search history, orders and unlocked reports.
- **Admin Dashboard** — manage users, credits, pricing, view searches/orders/messages, revenue stats.
- **Multi-language** — English (default), French, Haitian Creole.
- **Premium Apple-inspired UI** — blue & white theme, responsive, animated.

## Tech Stack

- Next.js 15 (App Router, API Routes) — no separate backend
- JavaScript + Tailwind CSS + shadcn/ui + lucide-react + framer-motion
- MongoDB (native driver)

## Getting Started

### 1. Install dependencies
```bash
yarn install   # or: npm install
```

### 2. Configure environment
Copy `.env.example` to `.env` and adjust values:
```bash
cp .env.example .env
```

### 3. Run the dev server
```bash
npm run dev
```
The app runs on http://localhost:3000

### 4. Build for production
```bash
npm run build
npm run start
```

## Default Admin Account

An admin user is seeded automatically on first run:

- **Email:** `admin@unlocktap.com`
- **Password:** `Admin@123`

New users receive **3 free credits** on registration.

## API Overview

All routes are served from the single catch-all handler at `app/api/[[...path]]/route.js` and are prefixed with `/api`.

| Method | Route | Description |
|--------|-------|-------------|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/forgot-password` | Request reset code (mock email) |
| POST | `/api/auth/reset-password` | Reset password |
| GET  | `/api/auth/me` | Current user |
| PUT  | `/api/profile` | Update profile |
| POST | `/api/imei/check` | IMEI free preview |
| POST | `/api/serial/check` | Serial free preview |
| POST | `/api/unlock` | Unlock premium report (1 credit) |
| GET  | `/api/history` | User search history |
| GET  | `/api/reports` | User unlocked reports |
| GET  | `/api/orders` | User orders |
| GET  | `/api/dashboard` | User dashboard stats |
| GET  | `/api/plans` | Credit plans |
| POST | `/api/checkout` | Mock purchase credits |
| POST | `/api/contact` | Contact form |
| GET/PUT | `/api/admin/*` | Admin management (users, plans, searches, orders, contacts, stats) |

## Database Collections

`users`, `plans`, `orders`, `searchhistory`, `reports`, `contacts`.

## Connecting Real Verification Providers

The mock engine lives in `route.js` (`generateIMEIReport` / `generateSerialReport`). To use a real provider, call it inside the `/imei/check`, `/serial/check` and `/unlock` handlers using the secure env vars: `IMEI_PROVIDER_API_KEY`, `IMEI_PROVIDER_URL`, `SERIAL_PROVIDER_API_KEY`, `SERIAL_PROVIDER_URL`. Keys are read server-side only and never exposed to the client.

## Deploying to Vercel

1. Push the repo to GitHub.
2. Import the project in Vercel.
3. Add the environment variables from `.env.example` (use a hosted MongoDB such as MongoDB Atlas for `MONGO_URL`).
4. Deploy.

## License

Demo project for Apple device verification. Provided as-is.
