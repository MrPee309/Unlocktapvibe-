import { MongoClient } from 'mongodb'
import { v4 as uuidv4 } from 'uuid'
import { NextResponse } from 'next/server'
import crypto from 'crypto'

// ------------------------------------------------------------------
// MongoDB connection (singleton)
// ------------------------------------------------------------------
let client
let db
let seeded = false

async function connectToMongo() {
  // Return cached DB only if a successful connection was previously established
  if (db) return db

  if (!process.env.MONGO_URL) {
    throw new Error('MONGO_URL environment variable is not set')
  }

  try {
    if (!client) {
      client = new MongoClient(process.env.MONGO_URL, {
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
  const { _id, password, ...rest } = u
  return rest
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
        hasMongoUrl: !!process.env.MONGO_URL,
        hasDbName: !!process.env.DB_NAME,
        dbName: process.env.DB_NAME || null,
        nodeEnv: process.env.NODE_ENV || null,
      }
      try {
        const d = await connectToMongo()
        await d.command({ ping: 1 })
        const usersCount = await d.collection('users').countDocuments()
        return json({ status: 'ok', db: 'connected', env: envInfo, usersCount })
      } catch (err) {
        // TEMPORARY diagnostic: surface the exact MongoDB connection error
        return json({
          status: 'error',
          db: 'connection_failed',
          env: envInfo,
          error: String(err && err.message ? err.message : err),
          name: err && err.name ? err.name : null,
          code: err && err.code ? err.code : null,
        }, 500)
      }
    }

    const db = await connectToMongo()

    // ---------------- AUTH ----------------
    if (route === '/auth/register' && method === 'POST') {
      const body = await request.json()
      const { name, username, country, phone, email, password } = body
      // Required field validation
      if (!name || !username || !country || !phone || !email || !password) {
        return json({ error: 'All fields are required' }, 400)
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
        createdAt: new Date(),
      }
      await db.collection('users').insertOne(user)
      const token = signToken({ sub: user.id, role: user.role })
      return json({ token, user: cleanUser(user) })
    }

    if (route === '/auth/login' && method === 'POST') {
      const { email, password } = await request.json()
      if (!email || !password) return json({ error: 'Email and password are required' }, 400)
      const user = await db.collection('users').findOne({ email: (email || '').toLowerCase() })
      if (!user || !verifyPassword(password, user.password)) return json({ error: 'Invalid email or password' }, 401)
      if (user.banned) return json({ error: 'This account has been suspended' }, 403)
      const token = signToken({ sub: user.id, role: user.role })
      return json({ token, user: cleanUser(user) })
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
