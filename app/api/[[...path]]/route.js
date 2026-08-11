
import { MongoClient } from 'mongodb'
import { v4 as uuidv4 } from 'uuid'
import { NextResponse } from 'next/server'
import crypto from 'crypto'
import nodemailer from 'nodemailer'

// ------------------------------------------------------------------
// MongoDB connection (singleton)
// ------------------------------------------------------------------
let client
let db
let seeded = false

// Canonical connection-string variable is MONGO_URL. We also accept MONGO_URI and
// MONGODB_URI as fallbacks so the app connects regardless of which name the hosting
// platform injects. Credentials are NEVER logged or returned anywhere.
function sanitizeUriValue(v) {
  if (!v) return ''
  let s = String(v).trim()
  // Strip a single layer of accidental wrapping quotes (a very common dashboard paste bug)
  if ((s.startsWith('"') && s.endsWith('"')) || (s.startsWith("'") && s.endsWith("'"))) {
    s = s.slice(1, -1).trim()
  }
  return s
}
function getMongoUri() {
  return sanitizeUriValue(process.env.MONGO_URL || process.env.MONGO_URI || process.env.MONGODB_URI || '')
}
function getMongoVarUsed() {
  if (process.env.MONGO_URL) return 'MONGO_URL'
  if (process.env.MONGO_URI) return 'MONGO_URI'
  if (process.env.MONGODB_URI) return 'MONGODB_URI'
  return null
}
// Safely describe the connection string WITHOUT leaking the password.
function maskMongoUri(uri) {
  if (!uri) return null
  try {
    const m = uri.match(/^(mongodb(?:\+srv)?:\/\/)(?:([^:@/]+)(?::([^@/]+))?@)?([^/?]+)(\/[^?]*)?(\?.*)?$/)
    if (!m) return { note: 'unparseable connection string' }
    return {
      scheme: m[1],
      username: m[2] || null,
      hasPassword: !!m[3],
      host: m[4] || null,
      pathDb: m[5] ? m[5].replace(/^\//, '') : null,
      hasQuery: !!m[6],
    }
  } catch {
    return { note: 'error parsing connection string' }
  }
}

// Remove any embedded credentials from an error message before returning it.
function sanitizeError(err) {
  let m = String(err && err.message ? err.message : err)
  // Redact userinfo in any URI that may appear inside driver error messages
  m = m.replace(/(mongodb(?:\+srv)?:\/\/)[^@\s]*@/gi, '$1<redacted>@')
  return m
}

// Parse the RAW connection string into SAFE, non-secret facts.
// Never returns the username value or password value.
function analyzeUriSafe(raw) {
  const info = {
    exists: !!raw,
    uriLength: raw ? raw.length : 0,
    hadWhitespaceEdges: false,
    hadWrappingQuotes: false,
    isSrvFormat: false,
    scheme: null,
    usernamePresent: false,
    usernameLength: 0,
    passwordPresent: false,
    passwordHasUnencodedSpecials: false,
    usernameHasUnencodedSpecials: false,
    host: null,
    databaseFromUri: null,
    hasQueryParams: false,
  }
  if (!raw) return info
  const trimmed = String(raw).trim()
  info.hadWhitespaceEdges = trimmed !== raw
  let s = trimmed
  if ((s.startsWith('"') && s.endsWith('"')) || (s.startsWith("'") && s.endsWith("'"))) {
    info.hadWrappingQuotes = true
    s = s.slice(1, -1).trim()
  }
  info.isSrvFormat = s.startsWith('mongodb+srv://')
  const schemeMatch = s.match(/^(mongodb(?:\+srv)?:\/\/)/)
  info.scheme = schemeMatch ? schemeMatch[1] : null
  if (!info.scheme) return info
  const rest = s.slice(info.scheme.length)
  const authorityEnd = rest.search(/[\/?]/)
  const authority = authorityEnd === -1 ? rest : rest.slice(0, authorityEnd)
  const afterAuthority = authorityEnd === -1 ? '' : rest.slice(authorityEnd)
  const lastAt = authority.lastIndexOf('@')
  let userinfo = ''
  let hostpart = authority
  if (lastAt !== -1) { userinfo = authority.slice(0, lastAt); hostpart = authority.slice(lastAt + 1) }
  info.host = hostpart || null
  if (userinfo) {
    const colon = userinfo.indexOf(':')
    const user = colon === -1 ? userinfo : userinfo.slice(0, colon)
    const pass = colon === -1 ? '' : userinfo.slice(colon + 1)
    // Characters that MUST be percent-encoded inside userinfo per RFC 3986 / Mongo docs
    const mustEncode = /[@:/?#[\]]/
    info.usernamePresent = !!user
    info.usernameLength = user ? user.length : 0
    info.passwordPresent = !!pass
    info.usernameHasUnencodedSpecials = mustEncode.test(user)
    info.passwordHasUnencodedSpecials = mustEncode.test(pass)
  }
  const q = afterAuthority.indexOf('?')
  const path = q === -1 ? afterAuthority : afterAuthority.slice(0, q)
  info.hasQueryParams = q !== -1
  const dbFromPath = path.replace(/^\//, '')
  info.databaseFromUri = dbFromPath || null
  return info
}

async function connectToMongo() {
  // Return cached DB only if a successful connection was previously established
  if (db) return db

  const uri = getMongoUri()
  if (!uri) {
    throw new Error('No MongoDB connection string found. Set MONGO_URL (or MONGO_URI) in the deployment environment variables.')
  }

  try {
    if (!client) {
      client = new MongoClient(uri, {
        serverSelectionTimeoutMS: 8000,
        connectTimeoutMS: 8000,
      })
    }
    await client.connect()
    // Verify the connection is actually usable
    await client.db(process.env.DB_NAME).command({ ping: 1 })
    db = client.db(process.env.DB_NAME)

    if (!seeded) {
      try {
        await seedData(db)
      } catch (seedErr) {
        // Seeding failure must not permanently break auth/API requests
        console.error('Seed error (non-fatal):', seedErr)
      }
      seeded = true
    }
    return db
  } catch (err) {
    // Reset cached client/db so the NEXT request retries a fresh connection
    // (prevents a failed cold-start from permanently returning 500s)
    try { await client?.close() } catch { /* ignore */ }
    client = null
    db = null
    throw err
  }
}

// ------------------------------------------------------------------
// Auth helpers (local credentials, Node crypto - no external service)
// ------------------------------------------------------------------
const AUTH_SECRET = process.env.AUTH_SECRET || 'unlocktap_dev_secret'

function b64url(input) {
  return Buffer.from(input).toString('base64').replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_')
}
function b64urlDecode(input) {
  input = input.replace(/-/g, '+').replace(/_/g, '/')
  while (input.length % 4) input += '='
  return Buffer.from(input, 'base64').toString()
}
function hashPassword(password) {
  const salt = crypto.randomBytes(16).toString('hex')
  const hash = crypto.pbkdf2Sync(password, salt, 100000, 64, 'sha512').toString('hex')
  return `${salt}:${hash}`
}
function verifyPassword(password, stored) {
  if (!stored || !stored.includes(':')) return false
  const [salt, hash] = stored.split(':')
  const check = crypto.pbkdf2Sync(password, salt, 100000, 64, 'sha512').toString('hex')
  return crypto.timingSafeEqual(Buffer.from(hash), Buffer.from(check))
}
function signToken(payload) {
  const body = { ...payload, exp: Date.now() + 1000 * 60 * 60 * 24 * 7 } // 7 days
  const data = b64url(JSON.stringify(body))
  const sig = crypto.createHmac('sha256', AUTH_SECRET).update(data).digest('base64')
    .replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_')
  return `${data}.${sig}`
}
function verifyToken(token) {
  try {
    if (!token) return null
    const [data, sig] = token.split('.')
    if (!data || !sig) return null
    const expected = crypto.createHmac('sha256', AUTH_SECRET).update(data).digest('base64')
      .replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_')
    if (expected !== sig) return null
    const payload = JSON.parse(b64urlDecode(data))
    if (payload.exp && Date.now() > payload.exp) return null
    return payload
  } catch {
    return null
  }
}
async function getUser(request, db) {
  const auth = request.headers.get('authorization') || ''
  const token = auth.startsWith('Bearer ') ? auth.slice(7) : null
  const payload = verifyToken(token)
  if (!payload) return null
  const user = await db.collection('users').findOne({ id: payload.sub })
  return user || null
}
function cleanUser(u) {
  if (!u) return null
  const { _id, password, verificationTokenHash, ...rest } = u
  return rest
}

// ------------------------------------------------------------------
// Email verification (real email, via SMTP - Node's crypto for tokens)
// ------------------------------------------------------------------
const VERIFICATION_TOKEN_TTL_MS = 24 * 60 * 60 * 1000 // 24 hours
const RESEND_COOLDOWN_MS = 60 * 1000 // 60 seconds between resend requests

function generateVerificationToken() {
  // 32 random bytes = cryptographically secure, unique, unguessable
  return crypto.randomBytes(32).toString('hex')
}
function hashVerificationToken(token) {
  // Only the hash is ever stored - the raw token exists only in the emailed link
  return crypto.createHash('sha256').update(token).digest('hex')
}

let mailTransport
let mailTransportError = null
function getMailTransport() {
  if (mailTransport || mailTransportError) return mailTransport
  const host = process.env.SMTP_HOST
  const port = Number(process.env.SMTP_PORT || 587)
  const user = process.env.SMTP_USER
  const pass = process.env.SMTP_PASS
  if (!host || !user || !pass) {
    mailTransportError = new Error(
      'Email is not configured. Set SMTP_HOST, SMTP_PORT, SMTP_USER and SMTP_PASS in the environment variables.'
    )
    return null
  }
  mailTransport = nodemailer.createTransport({
    host,
    port,
    secure: String(process.env.SMTP_SECURE || (port === 465 ? 'true' : 'false')) === 'true',
    auth: { user, pass },
  })
  return mailTransport
}

// Never leak SMTP credentials if the mail server error message happens to include them
function sanitizeMailError(err) {
  let m = String(err && err.message ? err.message : err)
  const pass = process.env.SMTP_PASS
  if (pass) m = m.split(pass).join('<redacted>')
  return m
}

function getAppUrl(request) {
  if (process.env.APP_URL) return process.env.APP_URL.replace(/\/$/, '')
  try {
    const origin = new URL(request.url).origin
    return origin
  } catch {
    return ''
  }
}

async function sendVerificationEmail({ to, name, token, request }) {
  const transport = getMailTransport()
  if (!transport) throw mailTransportError
  const verifyUrl = `${getAppUrl(request)}/?verify=${token}`
  const from = process.env.EMAIL_FROM || 'UnlockTap <no-reply@unlocktap.com>'
  const html = `
    <div style="font-family:Arial,Helvetica,sans-serif;max-width:480px;margin:0 auto;padding:24px;">
      <h2 style="color:#2563eb;margin-bottom:8px;">Verify your email</h2>
      <p>Hi ${name ? name.replace(/[<>]/g, '') : ''},</p>
      <p>Thanks for creating an UnlockTap account. Please confirm this is your email address by clicking the button below. This link expires in 24 hours.</p>
      <p style="text-align:center;margin:32px 0;">
        <a href="${verifyUrl}" style="background:#2563eb;color:#ffffff;text-decoration:none;padding:12px 28px;border-radius:10px;font-weight:bold;display:inline-block;">Verify Email</a>
      </p>
      <p style="font-size:12px;color:#64748b;">If the button doesn't work, copy and paste this link into your browser:<br/>${verifyUrl}</p>
      <p style="font-size:12px;color:#94a3b8;">If you didn't create this account, you can safely ignore this email.</p>
    </div>`
  const text = `Verify your UnlockTap account by visiting: ${verifyUrl}\nThis link expires in 24 hours.`
  try {
    await transport.sendMail({ from, to, subject: 'Verify your UnlockTap account', html, text })
  } catch (err) {
    throw new Error(sanitizeMailError(err))
  }
}

// ------------------------------------------------------------------
// Seeded RNG for deterministic mock reports
// ------------------------------------------------------------------
function seededRng(str) {
  let h = 1779033703 ^ str.length
  for (let i = 0; i < str.length; i++) {
    h = Math.imul(h ^ str.charCodeAt(i), 3432918353)
    h = (h << 13) | (h >>> 19)
  }
  let seed = (h >>> 0) || 1
  return function () {
    seed |= 0; seed = (seed + 0x6D2B79F5) | 0
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}
const pick = (rng, arr) => arr[Math.floor(rng() * arr.length)]

// ------------------------------------------------------------------
// Mock verification data
// ------------------------------------------------------------------
const IPHONE_MODELS = [
  { name: 'iPhone 15 Pro Max', number: 'A2849', ids: ['iPhone16,2'], caps: ['256GB', '512GB', '1TB'], colors: ['Natural Titanium', 'Blue Titanium', 'White Titanium', 'Black Titanium'] },
  { name: 'iPhone 15 Pro', number: 'A2848', ids: ['iPhone16,1'], caps: ['128GB', '256GB', '512GB'], colors: ['Natural Titanium', 'Blue Titanium', 'Black Titanium'] },
  { name: 'iPhone 15', number: 'A3090', ids: ['iPhone15,4'], caps: ['128GB', '256GB'], colors: ['Pink', 'Yellow', 'Green', 'Blue', 'Black'] },
  { name: 'iPhone 14 Pro Max', number: 'A2651', ids: ['iPhone15,3'], caps: ['128GB', '256GB', '512GB'], colors: ['Deep Purple', 'Gold', 'Silver', 'Space Black'] },
  { name: 'iPhone 14', number: 'A2649', ids: ['iPhone14,7'], caps: ['128GB', '256GB'], colors: ['Blue', 'Purple', 'Midnight', 'Starlight', 'Red'] },
  { name: 'iPhone 13', number: 'A2482', ids: ['iPhone14,5'], caps: ['128GB', '256GB', '512GB'], colors: ['Pink', 'Blue', 'Midnight', 'Starlight'] },
  { name: 'iPhone 12', number: 'A2172', ids: ['iPhone13,2'], caps: ['64GB', '128GB', '256GB'], colors: ['Black', 'White', 'Red', 'Blue', 'Green'] },
  { name: 'iPhone SE (3rd gen)', number: 'A2595', ids: ['iPhone14,6'], caps: ['64GB', '128GB'], colors: ['Midnight', 'Starlight', 'Red'] },
]
const CARRIERS = ['Unlocked', 'AT&T USA', 'T-Mobile USA', 'Verizon USA', 'Vodafone UK', 'Orange France', 'Bell Canada']
const COUNTRIES = ['United States', 'United Kingdom', 'Canada', 'France', 'Germany', 'Japan', 'Australia']

function generateIMEIReport(imei) {
  const rng = seededRng('imei:' + imei)
  const model = pick(rng, IPHONE_MODELS)
  const capacity = pick(rng, model.caps)
  const color = pick(rng, model.colors)
  const serial = generateSerialString(rng)
  const fmi = rng() > 0.6 ? 'ON' : 'OFF'
  const blacklist = rng() > 0.85 ? 'BLACKLISTED (Reported Lost/Stolen)' : 'CLEAN'
  const simlock = rng() > 0.5 ? 'Unlocked' : 'Locked'
  const purchaseYear = 2020 + Math.floor(rng() * 5)
  const purchaseMonth = 1 + Math.floor(rng() * 12)
  const purchaseDate = `${purchaseYear}-${String(purchaseMonth).padStart(2, '0')}-${String(1 + Math.floor(rng() * 27)).padStart(2, '0')}`
  const warrantyActive = purchaseYear >= 2023
  return {
    free: {
      'Brand': 'Apple',
      'Model': model.name,
      'Model Number': model.number,
      'Capacity': capacity,
      'Color': color,
    },
    premium: {
      'Serial Number': serial,
      'IMEI': imei,
      'IMEI2': (BigInt(imei) + 1n).toString(),
      'MEID': imei.slice(0, 14),
      'Model Identifier': model.ids[0],
      'Find My iPhone': fmi,
      'iCloud Status': fmi === 'ON' ? 'Locked (Activation Lock ON)' : 'Clean',
      'Blacklist Status': blacklist,
      'SIM-Lock Status': simlock,
      'Carrier': pick(rng, CARRIERS),
      'Country': pick(rng, COUNTRIES),
      'Warranty Status': warrantyActive ? 'Active - Limited Warranty' : 'Expired',
      'Estimated Purchase Date': purchaseDate,
      'AppleCare+ Eligible': warrantyActive ? 'Yes' : 'No',
      'Replaced Device': rng() > 0.9 ? 'Yes' : 'No',
      'Refurbished Device': rng() > 0.85 ? 'Yes' : 'No',
      'Demo Unit': rng() > 0.95 ? 'Yes' : 'No',
      'Loaner Device': 'No',
      'Purchase Country': pick(rng, COUNTRIES),
    },
  }
}

function generateSerialString(rng) {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ0123456789'
  let s = ''
  for (let i = 0; i < 10; i++) s += chars[Math.floor(rng() * chars.length)]
  return s
}

const APPLE_PRODUCTS = [
  { model: 'MacBook Pro 16-inch (2023)', id: 'Mac14,10', group: 'Mac', type: 'Notebook' },
  { model: 'MacBook Air 13-inch (M2, 2022)', id: 'Mac14,2', group: 'Mac', type: 'Notebook' },
  { model: 'iPad Pro 12.9-inch (6th gen)', id: 'iPad14,6', group: 'iPad', type: 'Tablet' },
  { model: 'iPad Air (5th gen)', id: 'iPad13,16', group: 'iPad', type: 'Tablet' },
  { model: 'Apple Watch Series 9', id: 'Watch7,1', group: 'Apple Watch', type: 'Wearable' },
  { model: 'iMac 24-inch (M3, 2023)', id: 'Mac15,4', group: 'Mac', type: 'Desktop' },
  { model: 'iPhone 14 Pro', id: 'iPhone15,2', group: 'iPhone', type: 'Smartphone' },
  { model: 'AirPods Pro (2nd gen)', id: 'AirPods14,1', group: 'AirPods', type: 'Audio' },
]

function generateSerialReport(serial) {
  const rng = seededRng('serial:' + serial)
  const product = pick(rng, APPLE_PRODUCTS)
  const mfgYear = 2020 + Math.floor(rng() * 5)
  const mfgMonth = 1 + Math.floor(rng() * 12)
  const purchaseDate = `${mfgYear}-${String(mfgMonth).padStart(2, '0')}-${String(1 + Math.floor(rng() * 27)).padStart(2, '0')}`
  const ageYears = 2025 - mfgYear
  const warrantyActive = ageYears < 1
  const coverageEnd = `${mfgYear + 1}-${String(mfgMonth).padStart(2, '0')}-15`
  return {
    free: {
      'Brand': 'Apple',
      'Model': product.model,
      'Group': product.group,
      'Type': product.type,
    },
    premium: {
      'Serial Number': serial,
      'Model Identifier': product.id,
      'Estimated Manufacture Date': purchaseDate,
      'Estimated Age': `${ageYears} year(s)`,
      'Valid Purchase Date': warrantyActive ? 'Yes' : 'Estimated',
      'Registration Status': rng() > 0.4 ? 'Registered' : 'Not Registered',
      'Warranty Status': warrantyActive ? 'Active - Limited Warranty' : 'Out of Warranty',
      'Repairs & Service Coverage': warrantyActive ? 'Active' : 'Expired',
      'Telephone Technical Support': warrantyActive ? 'Active' : 'Expired',
      'Coverage End Date': coverageEnd,
      'AppleCare+ Eligible': warrantyActive ? 'Yes' : 'No',
      'Country of Origin': pick(rng, COUNTRIES),
      'Replaced Device': rng() > 0.9 ? 'Yes' : 'No',
      'Refurbished': rng() > 0.85 ? 'Yes' : 'No',
    },
  }
}

// ------------------------------------------------------------------
// Seed default plans + admin
// ------------------------------------------------------------------
const DEFAULT_PLANS = [
  { id: 'single', name: 'Single Check', credits: 1, price: 2.99, popular: false, features: ['1 premium check', 'IMEI or Serial', 'Full report', 'Instant results'] },
  { id: 'starter', name: 'Starter', credits: 10, price: 14.99, popular: true, features: ['10 premium checks', 'IMEI & Serial', 'Full reports', 'Search history', 'Email support'] },
  { id: 'technician', name: 'Technician', credits: 50, price: 49.99, popular: false, features: ['50 premium checks', 'IMEI & Serial', 'Full reports', 'Priority processing', 'Priority support'] },
  { id: 'business', name: 'Business', credits: 200, price: 149.99, popular: false, features: ['200 premium checks', 'IMEI & Serial', 'Full reports', 'API placeholder access', 'Dedicated support'] },
]

async function seedData(db) {
  const plansCount = await db.collection('plans').countDocuments()
  if (plansCount === 0) {
    await db.collection('plans').insertMany(DEFAULT_PLANS.map(p => ({ ...p, createdAt: new Date() })))
  }
  const admin = await db.collection('users').findOne({ email: 'admin@unlocktap.com' })
  if (!admin) {
    await db.collection('users').insertOne({
      id: uuidv4(),
      name: 'UnlockTap Admin',
      email: 'admin@unlocktap.com',
      password: hashPassword('Admin@123'),
      role: 'admin',
      credits: 9999,
      language: 'en',
      banned: false,
      emailVerified: true, // seeded account - no verification email needed
      createdAt: new Date(),
    })
  }
}

// ------------------------------------------------------------------
// CORS
// ------------------------------------------------------------------
function handleCORS(response) {
  response.headers.set('Access-Control-Allow-Origin', process.env.CORS_ORIGINS || '*')
  response.headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
  response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization')
  response.headers.set('Access-Control-Allow-Credentials', 'true')
  return response
}
export async function OPTIONS() {
  return handleCORS(new NextResponse(null, { status: 200 }))
}
const json = (data, status = 200) => handleCORS(NextResponse.json(data, { status }))

// ------------------------------------------------------------------
// Main router
// ------------------------------------------------------------------
async function handleRoute(request, { params }) {
  const { path = [] } = await params
  const route = `/${path.join('/')}`
  const method = request.method

  try {
    // ---------------- Health (runs BEFORE DB connect so it can report the exact connection error) ----------------
    if (route === '/' && method === 'GET') {
      return json({ status: 'ok', service: 'UnlockTap API' })
    }
    if (route === '/health' && method === 'GET') {
      const envInfo = {
        mongoVarUsed: getMongoVarUsed(),
        hasMongoUrl: !!process.env.MONGO_URL,
        hasMongoUri: !!process.env.MONGO_URI,
        hasMongodbUri: !!process.env.MONGODB_URI,
        hasDbName: !!process.env.DB_NAME,
        dbName: process.env.DB_NAME || null,
        nodeEnv: process.env.NODE_ENV || null,
        connection: maskMongoUri(getMongoUri()), // password masked
      }
      try {
        const d = await connectToMongo()
        await d.command({ ping: 1 })
        const usersCount = await d.collection('users').countDocuments()
        return json({ status: 'ok', db: 'connected', env: envInfo, usersCount })
      } catch (err) {
        const message = String(err && err.message ? err.message : err)
        const code = err && err.code ? err.code : null
        // Targeted hint for the most common Atlas failures
        let hint = null
        if (/bad auth|authentication failed/i.test(message) || code === 8000) {
          hint = 'Atlas rejected the credentials. Verify the DB username & password in the connection string match a Database User in Atlas (Database Access), that the password is URL-encoded if it contains special characters (@ : / ? # [ ] %), and that the user has readWrite on the target database. Also confirm authSource (usually admin) is correct.'
        } else if (/ENOTFOUND|querySrv|getaddrinfo/i.test(message)) {
          hint = 'DNS/host resolution failed. Check the cluster host in the SRV connection string is correct.'
        } else if (/timed out|ETIMEDOUT|serverSelectionTimeout/i.test(message)) {
          hint = 'Connection timed out. In Atlas > Network Access, allow the deployment IP (or 0.0.0.0/0 for testing).'
        }
        // TEMPORARY diagnostic: surface the exact MongoDB connection error
        return json({
          status: 'error',
          db: 'connection_failed',
          env: envInfo,
          error: message,
          name: err && err.name ? err.name : null,
          code,
          hint,
        }, 500)
      }
    }

    // ---------------- DB DIAGNOSTIC (safe; runs a FRESH isolated connection attempt) ----------------
    // Attempts a brand-new connection using the EXACT process.env.MONGO_URL currently available
    // to the deployment, then reports ONLY safe facts + the stage where it failed.
    // Never returns the username value, password, or full connection string.
    if (route === '/db-diagnostic' && method === 'GET') {
      const rawEnv = process.env.MONGO_URL || process.env.MONGO_URI || process.env.MONGODB_URI || ''
      const analysis = analyzeUriSafe(rawEnv)
      const safe = {
        mongoUrlExists: !!process.env.MONGO_URL,
        variableUsed: getMongoVarUsed(),
        isSrvFormat: analysis.isSrvFormat,
        scheme: analysis.scheme,
        host: analysis.host,                       // hostname only, no credentials
        databaseFromUri: analysis.databaseFromUri, // db name in the URI path (if any)
        dbNameEnv: process.env.DB_NAME || null,
        effectiveDatabase: process.env.DB_NAME || analysis.databaseFromUri || '(driver default: test)',
        usernamePresent: analysis.usernamePresent,
        usernameLength: analysis.usernameLength,   // length only, not the value
        passwordPresent: analysis.passwordPresent,
        passwordHasUnencodedSpecials: analysis.passwordHasUnencodedSpecials,
        usernameHasUnencodedSpecials: analysis.usernameHasUnencodedSpecials,
        hadWhitespaceEdges: analysis.hadWhitespaceEdges,
        hadWrappingQuotes: analysis.hadWrappingQuotes,
        uriLength: analysis.uriLength,
      }

      if (!rawEnv) {
        return json({ status: 'error', connection: 'failed', failureStage: 'missing_env', message: 'No MongoDB connection string found in MONGO_URL / MONGO_URI / MONGODB_URI.', ...safe }, 500)
      }

      // Use the sanitized value (trim + strip wrapping quotes) â the same value the app now uses.
      const testUri = sanitizeUriValue(rawEnv)
      let stage = 'uri_parse'
      let testClient = null
      try {
        testClient = new MongoClient(testUri, { serverSelectionTimeoutMS: 6000, connectTimeoutMS: 6000 })
        stage = 'dns_tls_network'   // parsing succeeded; connect performs DNS/TLS + auth handshake
        await testClient.connect()
        stage = 'authentication'    // if connect resolved, the auth handshake also succeeded
        await testClient.db(process.env.DB_NAME).command({ ping: 1 })
        await testClient.close()
        return json({ status: 'ok', connection: 'success', failureStage: null, ...safe })
      } catch (err) {
        try { await testClient?.close() } catch { /* ignore */ }
        const msg = sanitizeError(err)
        const code = err && err.code ? err.code : null
        const name = err && err.name ? err.name : null
        // Classify WHERE it failed: uri_parse | dns_tls_network | authentication
        let failureStage = stage
        if (name === 'MongoParseError' || /invalid connection string|uri malformed|parse/i.test(msg)) {
          failureStage = 'uri_parse'
        } else if (/bad auth|authentication failed|AuthenticationFailed|SCRAM|not authorized/i.test(msg) || code === 8000 || code === 18) {
          failureStage = 'authentication'
        } else if (/ENOTFOUND|querySrv|getaddrinfo|ETIMEDOUT|ECONNREFUSED|TLS|SSL|server selection|ServerSelection|topology|network/i.test(msg)) {
          failureStage = 'dns_tls_network'
        }
        let hint = null
        if (failureStage === 'authentication') {
          hint = analysis.passwordHasUnencodedSpecials
            ? 'AUTH failed AND the password contains characters that must be percent-encoded (@ : / ? # [ ]). This is the most likely cause: URL-encode the password in MONGO_URL (e.g. @ -> %40, # -> %23, / -> %2F).'
            : 'AUTH handshake reached Atlas but credentials were rejected. The DB username/password in MONGO_URL do not match a Database User in Atlas, OR the user lacks access to this database/authSource. Confirm the exact username and that the new password value in Vercel matches the one saved in Atlas (no trailing spaces).'
        } else if (failureStage === 'uri_parse') {
          hint = 'The connection string could not be parsed. Check for stray quotes/spaces (hadWrappingQuotes/hadWhitespaceEdges), unencoded special characters in the password, or a malformed query string.'
        } else if (failureStage === 'dns_tls_network') {
          hint = 'Reached before authentication: DNS/TLS/network. Verify the cluster host and that Atlas Network Access allows the deployment IP (0.0.0.0/0 for testing).'
        }
        return json({ status: 'error', connection: 'failed', failureStage, error: msg, code, name, hint, ...safe }, 500)
      }
    }

    const db = await connectToMongo()

    // ---------------- AUTH ----------------
    if (route === '/auth/register' && method === 'POST') {
      const body = await request.json()
      const { name, username, country, phone, email, password, termsAccepted } = body
      // Required field validation
      if (!name || !username || !country || !phone || !email || !password) {
        return json({ error: 'All fields are required' }, 400)
      }
      // Terms & Conditions acceptance is MANDATORY (enforced server-side; cannot be bypassed via direct API call)
      if (termsAccepted !== true) {
        return json({ error: 'You must agree to the Terms & Conditions and Privacy Policy to create an account.' }, 400)
      }
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return json({ error: 'Invalid email address' }, 400)
      if (!/^[a-zA-Z0-9_]{3,20}$/.test(username)) {
        return json({ error: 'Username must be 3-20 characters (letters, numbers, underscore only)' }, 400)
      }
      if (!/^[+\d][\d\s()\-]{6,19}$/.test(phone)) return json({ error: 'Invalid phone number' }, 400)
      if (password.length < 6) return json({ error: 'Password must be at least 6 characters' }, 400)
      // Duplicate email check
      const emailExists = await db.collection('users').findOne({ email: email.toLowerCase() })
      if (emailExists) return json({ error: 'An account with this email already exists' }, 409)
      // Duplicate username check (case-insensitive)
      const escaped = username.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
      const usernameExists = await db.collection('users').findOne({ username: { $regex: `^${escaped}$`, $options: 'i' } })
      if (usernameExists) return json({ error: 'This username is already taken' }, 409)
      // Account is created unverified. NO session/token is issued here - the client
      // stays logged out until the real verification email is confirmed.
      const verificationToken = generateVerificationToken()
      const user = {
        id: uuidv4(),
        name,
        username,
        country,
        phone,
        email: email.toLowerCase(),
        password: hashPassword(password), // never stored/returned in plaintext
        role: 'user',
        credits: 3, // free welcome credits
        language: body.language || 'en',
        banned: false,
        termsAccepted: true,
        termsAcceptedAt: new Date(),
        emailVerified: false,
        verificationTokenHash: hashVerificationToken(verificationToken),
        verificationTokenExpiresAt: new Date(Date.now() + VERIFICATION_TOKEN_TTL_MS),
        createdAt: new Date(),
      }
      await db.collection('users').insertOne(user)

      try {
        await sendVerificationEmail({ to: user.email, name: user.name, token: verificationToken, request })
        await db.collection('users').updateOne({ id: user.id }, { $set: { verificationLastSentAt: new Date() } })
      } catch (err) {
        // Never claim an email was sent when it wasn't - roll back the account instead
        // of leaving an unverifiable, unusable user record behind.
        await db.collection('users').deleteOne({ id: user.id })
        console.error('Verification email send failed:', err.message)
        return json({ error: 'We could not send the verification email right now. Please try registering again shortly.' }, 502)
      }

      // No token, no user session - client remains logged out.
      return json({
        message: 'Account created. Please check your email to verify your account before logging in.',
        email: user.email,
      }, 201)
    }

    if (route === '/auth/login' && method === 'POST') {
      const { email, password } = await request.json()
      if (!email || !password) return json({ error: 'Email and password are required' }, 400)
      const user = await db.collection('users').findOne({ email: (email || '').toLowerCase() })
      if (!user || !verifyPassword(password, user.password)) return json({ error: 'Invalid email or password' }, 401)
      if (user.banned) return json({ error: 'This account has been suspended' }, 403)
      // Only block accounts explicitly marked unverified - accounts created before this
      // feature existed have no `emailVerified` field and continue to log in normally.
      if (user.emailVerified === false) {
        return json({ error: 'Please verify your email before logging in.', code: 'EMAIL_NOT_VERIFIED' }, 403)
      }
      const token = signToken({ sub: user.id, role: user.role })
      return json({ token, user: cleanUser(user) })
    }

    if (route === '/auth/verify-email' && method === 'POST') {
      const { token } = await request.json()
      if (!token || typeof token !== 'string') return json({ error: 'Verification token is required' }, 400)
      const tokenHash = hashVerificationToken(token)
      const user = await db.collection('users').findOne({ verificationTokenHash: tokenHash })
      if (!user || !user.verificationTokenExpiresAt || new Date(user.verificationTokenExpiresAt) < new Date()) {
        return json({ error: 'This verification link is invalid or has expired. Please request a new one.' }, 400)
      }
      // Token is invalidated (one-time-use) whether or not the account was already verified
      await db.collection('users').updateOne(
        { id: user.id },
        { $set: { emailVerified: true }, $unset: { verificationTokenHash: '', verificationTokenExpiresAt: '' } }
      )
      return json({ message: 'Your email has been verified. You can now log in.' })
    }

    if (route === '/auth/resend-verification' && method === 'POST') {
      const { email } = await request.json()
      if (!email) return json({ error: 'Email is required' }, 400)
      const user = await db.collection('users').findOne({ email: (email || '').toLowerCase() })
      if (!user) return json({ error: 'No account found with this email address' }, 404)
      if (user.emailVerified !== false) {
        return json({ message: 'This account is already verified. You can log in.' })
      }
      if (user.verificationLastSentAt) {
        const elapsed = Date.now() - new Date(user.verificationLastSentAt).getTime()
        if (elapsed < RESEND_COOLDOWN_MS) {
          const retryAfterSeconds = Math.ceil((RESEND_COOLDOWN_MS - elapsed) / 1000)
          return json({ error: `Please wait ${retryAfterSeconds}s before requesting another verification email.`, retryAfterSeconds }, 429)
        }
      }
      const verificationToken = generateVerificationToken()
      await db.collection('users').updateOne(
        { id: user.id },
        { $set: {
          verificationTokenHash: hashVerificationToken(verificationToken),
          verificationTokenExpiresAt: new Date(Date.now() + VERIFICATION_TOKEN_TTL_MS),
        } }
      )
      try {
        await sendVerificationEmail({ to: user.email, name: user.name, token: verificationToken, request })
      } catch (err) {
        // Do not set verificationLastSentAt on failure, so the user can retry immediately
        console.error('Resend verification email failed:', err.message)
        return json({ error: 'We could not send the verification email right now. Please try again shortly.' }, 502)
      }
      await db.collection('users').updateOne({ id: user.id }, { $set: { verificationLastSentAt: new Date() } })
      return json({ message: 'Verification email sent. Please check your inbox.' })
    }

    if (route === '/auth/forgot-password' && method === 'POST') {
      const { email } = await request.json()
      const user = await db.collection('users').findOne({ email: (email || '').toLowerCase() })
      // Mock: always succeed. If user exists, generate a reset token.
      const resetToken = user ? crypto.randomBytes(4).toString('hex').toUpperCase() : null
      if (user) {
        await db.collection('users').updateOne({ id: user.id }, { $set: { resetToken } })
      }
      return json({
        message: 'If an account exists, a reset code has been sent.',
        // In this demo (mock email), we return the code directly to allow reset flow.
        demoResetCode: resetToken,
      })
    }

    if (route === '/auth/reset-password' && method === 'POST') {
      const { email, code, password } = await request.json()
      if (!email || !code || !password) return json({ error: 'All fields are required' }, 400)
      const user = await db.collection('users').findOne({ email: (email || '').toLowerCase() })
      if (!user || user.resetToken !== code) return json({ error: 'Invalid reset code' }, 400)
      await db.collection('users').updateOne({ id: user.id }, { $set: { password: hashPassword(password) }, $unset: { resetToken: '' } })
      return json({ message: 'Password reset successful. You can now log in.' })
    }

    if (route === '/auth/me' && method === 'GET') {
      const user = await getUser(request, db)
      if (!user) return json({ error: 'Unauthorized' }, 401)
      return json({ user: cleanUser(user) })
    }

    // ---------------- PROFILE ----------------
    if (route === '/profile' && method === 'PUT') {
      const user = await getUser(request, db)
      if (!user) return json({ error: 'Unauthorized' }, 401)
      const body = await request.json()
      const update = {}
      if (body.name) update.name = body.name
      if (body.language) update.language = body.language
      if (body.password) {
        if (body.password.length < 6) return json({ error: 'Password must be at least 6 characters' }, 400)
        update.password = hashPassword(body.password)
      }
      await db.collection('users').updateOne({ id: user.id }, { $set: update })
      const updated = await db.collection('users').findOne({ id: user.id })
      return json({ user: cleanUser(updated) })
    }

    // ---------------- CHECK (IMEI / SERIAL) ----------------
    if (route === '/imei/check' && method === 'POST') {
      const { imei } = await request.json()
      const clean = (imei || '').replace(/\s|-/g, '')
      if (!/^\d{15}$/.test(clean)) return json({ error: 'IMEI must be exactly 15 digits' }, 400)
      const report = generateIMEIReport(clean)
      const user = await getUser(request, db)
      const search = {
        id: uuidv4(),
        userId: user ? user.id : null,
        type: 'imei',
        query: clean,
        model: report.free['Model'],
        unlocked: false,
        createdAt: new Date(),
      }
      await db.collection('searchhistory').insertOne(search)
      return json({ searchId: search.id, type: 'imei', query: clean, free: report.free, locked: true })
    }

    if (route === '/serial/check' && method === 'POST') {
      const { serial } = await request.json()
      const clean = (serial || '').trim().toUpperCase()
      if (!/^[A-Z0-9]{8,14}$/.test(clean)) return json({ error: 'Invalid Apple serial number (8-14 alphanumeric characters)' }, 400)
      const report = generateSerialReport(clean)
      const user = await getUser(request, db)
      const search = {
        id: uuidv4(),
        userId: user ? user.id : null,
        type: 'serial',
        query: clean,
        model: report.free['Model'],
        unlocked: false,
        createdAt: new Date(),
      }
      await db.collection('searchhistory').insertOne(search)
      return json({ searchId: search.id, type: 'serial', query: clean, free: report.free, locked: true })
    }

    // Unlock premium report (spends 1 credit)
    if (route === '/unlock' && method === 'POST') {
      const user = await getUser(request, db)
      if (!user) return json({ error: 'Please log in to unlock premium reports' }, 401)
      const { searchId } = await request.json()
      const search = await db.collection('searchhistory').findOne({ id: searchId })
      if (!search) return json({ error: 'Search not found' }, 404)
      // Re-generate premium data deterministically
      const report = search.type === 'imei' ? generateIMEIReport(search.query) : generateSerialReport(search.query)

      if (!search.unlocked) {
        if (user.credits < 1) return json({ error: 'Insufficient credits. Please buy a credit pack.', code: 'NO_CREDITS' }, 402)
        await db.collection('users').updateOne({ id: user.id }, { $inc: { credits: -1 } })
        await db.collection('searchhistory').updateOne({ id: searchId }, { $set: { unlocked: true, userId: user.id } })
        // Create a report record
        await db.collection('reports').insertOne({
          id: uuidv4(),
          userId: user.id,
          searchId,
          type: search.type,
          query: search.query,
          model: search.model,
          data: { ...report.free, ...report.premium },
          createdAt: new Date(),
        })
      }
      const updatedUser = await db.collection('users').findOne({ id: user.id })
      return json({ free: report.free, premium: report.premium, credits: updatedUser.credits })
    }

    // ---------------- HISTORY / REPORTS / ORDERS / DASHBOARD ----------------
    if (route === '/history' && method === 'GET') {
      const user = await getUser(request, db)
      if (!user) return json({ error: 'Unauthorized' }, 401)
      const items = await db.collection('searchhistory').find({ userId: user.id }).sort({ createdAt: -1 }).limit(200).toArray()
      return json({ items: items.map(({ _id, ...r }) => r) })
    }

    if (route === '/reports' && method === 'GET') {
      const user = await getUser(request, db)
      if (!user) return json({ error: 'Unauthorized' }, 401)
      const items = await db.collection('reports').find({ userId: user.id }).sort({ createdAt: -1 }).limit(200).toArray()
      return json({ items: items.map(({ _id, ...r }) => r) })
    }

    if (route === '/orders' && method === 'GET') {
      const user = await getUser(request, db)
      if (!user) return json({ error: 'Unauthorized' }, 401)
      const items = await db.collection('orders').find({ userId: user.id }).sort({ createdAt: -1 }).limit(200).toArray()
      return json({ items: items.map(({ _id, ...r }) => r) })
    }

    if (route === '/dashboard' && method === 'GET') {
      const user = await getUser(request, db)
      if (!user) return json({ error: 'Unauthorized' }, 401)
      const [searches, reports, orders] = await Promise.all([
        db.collection('searchhistory').countDocuments({ userId: user.id }),
        db.collection('reports').countDocuments({ userId: user.id }),
        db.collection('orders').countDocuments({ userId: user.id }),
      ])
      const recent = await db.collection('searchhistory').find({ userId: user.id }).sort({ createdAt: -1 }).limit(5).toArray()
      return json({
        stats: { credits: user.credits, searches, reports, orders },
        recent: recent.map(({ _id, ...r }) => r),
      })
    }

    // ---------------- PLANS / CHECKOUT (mock payment) ----------------
    if (route === '/plans' && method === 'GET') {
      const plans = await db.collection('plans').find({}).sort({ price: 1 }).toArray()
      return json({ plans: plans.map(({ _id, ...p }) => p) })
    }

    if (route === '/checkout' && method === 'POST') {
      const user = await getUser(request, db)
      if (!user) return json({ error: 'Please log in to purchase credits' }, 401)
      const { planId } = await request.json()
      const plan = await db.collection('plans').findOne({ id: planId })
      if (!plan) return json({ error: 'Plan not found' }, 404)
      // MOCK PAYMENT - always succeeds
      const order = {
        id: uuidv4(),
        userId: user.id,
        planId: plan.id,
        planName: plan.name,
        credits: plan.credits,
        amount: plan.price,
        status: 'paid',
        paymentMethod: 'mock',
        createdAt: new Date(),
      }
      await db.collection('orders').insertOne(order)
      await db.collection('users').updateOne({ id: user.id }, { $inc: { credits: plan.credits } })
      const updated = await db.collection('users').findOne({ id: user.id })
      const { _id, ...cleanOrder } = order
      return json({ order: cleanOrder, credits: updated.credits, message: `Payment successful! ${plan.credits} credits added.` })
    }

    // ---------------- CONTACT ----------------
    if (route === '/contact' && method === 'POST') {
      const { name, email, message } = await request.json()
      if (!name || !email || !message) return json({ error: 'All fields are required' }, 400)
      await db.collection('contacts').insertOne({ id: uuidv4(), name, email, message, status: 'new', createdAt: new Date() })
      return json({ message: 'Thank you! We will get back to you soon.' })
    }

    // ---------------- ADMIN ----------------
    if (route.startsWith('/admin')) {
      const user = await getUser(request, db)
      if (!user) return json({ error: 'Unauthorized' }, 401)
      if (user.role !== 'admin') return json({ error: 'Forbidden - admin only' }, 403)

      if (route === '/admin/stats' && method === 'GET') {
        const [users, searches, reports, orders, contacts] = await Promise.all([
          db.collection('users').countDocuments(),
          db.collection('searchhistory').countDocuments(),
          db.collection('reports').countDocuments(),
          db.collection('orders').countDocuments(),
          db.collection('contacts').countDocuments(),
        ])
        const allOrders = await db.collection('orders').find({ status: 'paid' }).toArray()
        const revenue = allOrders.reduce((s, o) => s + (o.amount || 0), 0)
        return json({ stats: { users, searches, reports, orders, contacts, revenue: Math.round(revenue * 100) / 100 } })
      }
      if (route === '/admin/users' && method === 'GET') {
        const items = await db.collection('users').find({}).sort({ createdAt: -1 }).toArray()
        return json({ items: items.map(cleanUser) })
      }
      if (route.startsWith('/admin/users/') && method === 'PUT') {
        const id = path[2]
        const body = await request.json()
        const update = {}
        if (typeof body.credits === 'number') update.credits = body.credits
        if (body.role) update.role = body.role
        if (typeof body.banned === 'boolean') update.banned = body.banned
        await db.collection('users').updateOne({ id }, { $set: update })
        const updated = await db.collection('users').findOne({ id })
        return json({ user: cleanUser(updated) })
      }
      if (route.startsWith('/admin/users/') && method === 'DELETE') {
        const id = path[2]
        await db.collection('users').deleteOne({ id })
        return json({ message: 'User deleted' })
      }
      if (route === '/admin/searches' && method === 'GET') {
        const items = await db.collection('searchhistory').find({}).sort({ createdAt: -1 }).limit(500).toArray()
        return json({ items: items.map(({ _id, ...r }) => r) })
      }
      if (route === '/admin/reports' && method === 'GET') {
        const items = await db.collection('reports').find({}).sort({ createdAt: -1 }).limit(500).toArray()
        return json({ items: items.map(({ _id, ...r }) => r) })
      }
      if (route === '/admin/orders' && method === 'GET') {
        const items = await db.collection('orders').find({}).sort({ createdAt: -1 }).limit(500).toArray()
        return json({ items: items.map(({ _id, ...r }) => r) })
      }
      if (route === '/admin/contacts' && method === 'GET') {
        const items = await db.collection('contacts').find({}).sort({ createdAt: -1 }).limit(500).toArray()
        return json({ items: items.map(({ _id, ...r }) => r) })
      }
      if (route === '/admin/plans' && method === 'GET') {
        const items = await db.collection('plans').find({}).sort({ price: 1 }).toArray()
        return json({ items: items.map(({ _id, ...r }) => r) })
      }
      if (route.startsWith('/admin/plans/') && method === 'PUT') {
        const id = path[2]
        const body = await request.json()
        const update = {}
        if (body.name) update.name = body.name
        if (typeof body.credits === 'number') update.credits = body.credits
        if (typeof body.price === 'number') update.price = body.price
        if (typeof body.popular === 'boolean') update.popular = body.popular
        await db.collection('plans').updateOne({ id }, { $set: update })
        const updated = await db.collection('plans').findOne({ id })
        const { _id, ...clean } = updated
        return json({ plan: clean })
      }
    }

    return json({ error: `Route ${route} not found` }, 404)
  } catch (error) {
    console.error('API Error:', error)
    return json({ error: 'Internal server error' }, 500)
  }
}

export const GET = handleRoute
export const POST = handleRoute
export const PUT = handleRoute
export const DELETE = handleRoute
export const PATCH = handleRoute
