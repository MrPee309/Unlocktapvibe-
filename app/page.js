'use client'

import { useEffect, useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import {
  Smartphone, ShieldCheck, Search, Lock, Zap, Globe, CheckCircle2, XCircle,
  CreditCard, LayoutDashboard, LogOut, User as UserIcon, Menu, X, Star,
  Cpu, Fingerprint, ScanLine, ChevronRight, Mail, Sparkles, BadgeCheck,
  Users, FileText, Settings, DollarSign, History, Loader2, Apple,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from '@/components/ui/accordion'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Separator } from '@/components/ui/separator'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Toaster } from '@/components/ui/sonner'
import { toast } from 'sonner'

const HERO_IMG = 'https://images.unsplash.com/photo-1592750475338-74b7b21085ab?auto=format&fit=crop&w=1200&q=80'
const CTA_IMG = 'https://images.unsplash.com/photo-1621768216002-5ac171876625?auto=format&fit=crop&w=1200&q=80'

const COUNTRIES_LIST = [
  'United States', 'United Kingdom', 'Canada', 'France', 'Germany', 'Spain', 'Italy',
  'Netherlands', 'Belgium', 'Switzerland', 'Portugal', 'Ireland', 'Sweden', 'Norway',
  'Denmark', 'Finland', 'Poland', 'Austria', 'Greece', 'Haiti', 'Dominican Republic',
  'Mexico', 'Brazil', 'Argentina', 'Chile', 'Colombia', 'Peru', 'Jamaica', 'Trinidad and Tobago',
  'Australia', 'New Zealand', 'Japan', 'China', 'South Korea', 'India', 'Singapore',
  'United Arab Emirates', 'Saudi Arabia', 'Qatar', 'South Africa', 'Nigeria', 'Kenya',
  'Egypt', 'Morocco', 'Turkey', 'Israel', 'Other',
]

// ------------------------------------------------------------------
// i18n
// ------------------------------------------------------------------
const T = {
  en: {
    nav_home: 'Home', nav_imei: 'IMEI Checker', nav_serial: 'Serial Checker', nav_pricing: 'Pricing',
    nav_faq: 'FAQ', nav_contact: 'Contact', login: 'Login', register: 'Register', logout: 'Logout',
    dashboard: 'Dashboard', profile: 'Profile', admin: 'Admin', credits: 'Credits',
    hero_badge: 'Trusted Apple Device Verification',
    hero_title: 'Check any Apple device in seconds',
    hero_sub: 'Instant IMEI & Serial number lookups. Verify iCloud lock, warranty, carrier, blacklist status and more — powered by a premium verification engine.',
    hero_cta1: 'Check IMEI', hero_cta2: 'Check Serial Number',
    features_title: 'Everything you need to verify a device',
    features_sub: 'Professional-grade checks trusted by technicians and resellers worldwide.',
    pricing_title: 'Simple, transparent pricing', pricing_sub: 'Pay only for what you use. Credits never expire.',
    testi_title: 'Loved by resellers & repair shops',
    faq_title: 'Frequently asked questions',
    footer_tag: 'Premium Apple device verification made simple.',
    get_started: 'Get Started', buy_credits: 'Buy Credits', most_popular: 'Most Popular',
    free_preview: 'Free Preview', premium_report: 'Premium Report', unlock_report: 'Unlock Full Report (1 credit)',
    check_now: 'Check Now', enter_imei: 'Enter 15-digit IMEI', enter_serial: 'Enter Apple Serial Number',
    email: 'Email', password: 'Password', name: 'Full Name', forgot: 'Forgot password?',
    no_account: "Don't have an account?", have_account: 'Already have an account?',
    search_history: 'Search History', orders: 'Orders', reports: 'Reports', overview: 'Overview',
    welcome_back: 'Welcome back', signin_sub: 'Sign in to access your dashboard and credits',
    create_account: 'Create your account', register_sub: 'Get 3 free credits when you sign up',
    send_message: 'Send Message', contact_title: 'Get in touch', contact_sub: 'We usually respond within 24 hours.',
    language: 'Language',
  },
  fr: {
    nav_home: 'Accueil', nav_imei: 'Vérif IMEI', nav_serial: 'Vérif Série', nav_pricing: 'Tarifs',
    nav_faq: 'FAQ', nav_contact: 'Contact', login: 'Connexion', register: 'S’inscrire', logout: 'Déconnexion',
    dashboard: 'Tableau de bord', profile: 'Profil', admin: 'Admin', credits: 'Crédits',
    hero_badge: 'Vérification de confiance des appareils Apple',
    hero_title: 'Vérifiez tout appareil Apple en quelques secondes',
    hero_sub: 'Recherche instantanée IMEI & numéro de série. Vérifiez le verrou iCloud, la garantie, l’opérateur, la liste noire et plus encore.',
    hero_cta1: 'Vérifier IMEI', hero_cta2: 'Vérifier numéro de série',
    features_title: 'Tout ce qu’il faut pour vérifier un appareil',
    features_sub: 'Des vérifications professionnelles utilisées par les techniciens et revendeurs du monde entier.',
    pricing_title: 'Tarifs simples et transparents', pricing_sub: 'Payez seulement ce que vous utilisez. Les crédits n’expirent jamais.',
    testi_title: 'Adoré par les revendeurs et réparateurs',
    faq_title: 'Questions fréquentes',
    footer_tag: 'La vérification Apple premium, simplifiée.',
    get_started: 'Commencer', buy_credits: 'Acheter des crédits', most_popular: 'Le plus populaire',
    free_preview: 'Aperçu gratuit', premium_report: 'Rapport premium', unlock_report: 'Débloquer le rapport (1 crédit)',
    check_now: 'Vérifier', enter_imei: 'Entrez l’IMEI à 15 chiffres', enter_serial: 'Entrez le numéro de série Apple',
    email: 'Email', password: 'Mot de passe', name: 'Nom complet', forgot: 'Mot de passe oublié ?',
    no_account: 'Pas de compte ?', have_account: 'Déjà un compte ?',
    search_history: 'Historique', orders: 'Commandes', reports: 'Rapports', overview: 'Aperçu',
    welcome_back: 'Bon retour', signin_sub: 'Connectez-vous pour accéder à votre tableau de bord',
    create_account: 'Créez votre compte', register_sub: 'Obtenez 3 crédits gratuits à l’inscription',
    send_message: 'Envoyer', contact_title: 'Contactez-nous', contact_sub: 'Nous répondons sous 24 heures.',
    language: 'Langue',
  },
  ht: {
    nav_home: 'Akèy', nav_imei: 'Tcheke IMEI', nav_serial: 'Tcheke Seri', nav_pricing: 'Pri',
    nav_faq: 'FAQ', nav_contact: 'Kontak', login: 'Konekte', register: 'Enskri', logout: 'Dekonekte',
    dashboard: 'Tablo', profile: 'Pwofil', admin: 'Admin', credits: 'Kredi',
    hero_badge: 'Verifikasyon aparèy Apple ou ka fè konfyans',
    hero_title: 'Tcheke nenpòt aparèy Apple nan segond',
    hero_sub: 'Rechèch IMEI & nimewo seri touswit. Verifye vèwou iCloud, garanti, konpayi, lis nwa ak plis ankò.',
    hero_cta1: 'Tcheke IMEI', hero_cta2: 'Tcheke nimewo seri',
    features_title: 'Tout sa ou bezwen pou verifye yon aparèy',
    features_sub: 'Verifikasyon pwofesyonèl teknisyen ak revandè atravè mond lan fè konfyans.',
    pricing_title: 'Pri senp e klè', pricing_sub: 'Peye sèlman sa ou itilize. Kredi pa janm ekspire.',
    testi_title: 'Revandè ak boutik reparasyon renmen li',
    faq_title: 'Kesyon yo poze souvan',
    footer_tag: 'Verifikasyon Apple premium, senp.',
    get_started: 'Kòmanse', buy_credits: 'Achte Kredi', most_popular: 'Pi Popilè',
    free_preview: 'Apèsi Gratis', premium_report: 'Rapò Premium', unlock_report: 'Debloke Rapò a (1 kredi)',
    check_now: 'Tcheke Kounye a', enter_imei: 'Antre IMEI 15 chif', enter_serial: 'Antre nimewo seri Apple',
    email: 'Imèl', password: 'Modpas', name: 'Non konplè', forgot: 'Bliye modpas?',
    no_account: 'Ou pa gen kont?', have_account: 'Ou gen yon kont deja?',
    search_history: 'Istwa Rechèch', orders: 'Kòmand', reports: 'Rapò', overview: 'Apèsi',
    welcome_back: 'Byenveni ankò', signin_sub: 'Konekte pou aksede tablo ou',
    create_account: 'Kreye kont ou', register_sub: 'Jwenn 3 kredi gratis lè ou enskri',
    send_message: 'Voye Mesaj', contact_title: 'Kontakte nou', contact_sub: 'Nou reponn nan 24 èdtan.',
    language: 'Lang',
  },
}

// ------------------------------------------------------------------
// API helper
// ------------------------------------------------------------------
async function api(path, { method = 'GET', body, token } = {}) {
  const headers = { 'Content-Type': 'application/json' }
  if (token) headers['Authorization'] = `Bearer ${token}`
  const res = await fetch(`/api${path}`, { method, headers, body: body ? JSON.stringify(body) : undefined })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw Object.assign(new Error(data.error || 'Request failed'), { data, status: res.status })
  return data
}

// ==================================================================
// Root App
// ==================================================================
export default function App() {
  const [route, setRoute] = useState('home')
  const [routeParam, setRouteParam] = useState(null)
  const [token, setToken] = useState(null)
  const [user, setUser] = useState(null)
  const [lang, setLang] = useState('en')
  const [ready, setReady] = useState(false)

  const t = (k) => (T[lang] && T[lang][k]) || T.en[k] || k

  const navigate = useCallback((r, param = null) => {
    setRoute(r); setRouteParam(param)
    if (typeof window !== 'undefined') window.scrollTo({ top: 0, behavior: 'smooth' })
  }, [])

  const refreshUser = useCallback(async (tk) => {
    try { const { user } = await api('/auth/me', { token: tk }); setUser(user) } catch { /* ignore */ }
  }, [])

  useEffect(() => {
    const tk = localStorage.getItem('ut_token')
    const lg = localStorage.getItem('ut_lang')
    if (lg) setLang(lg)
    if (tk) { setToken(tk); refreshUser(tk).finally(() => setReady(true)) } else { setReady(true) }
  }, [refreshUser])

  const setAuth = (tk, u) => {
    setToken(tk); setUser(u); localStorage.setItem('ut_token', tk)
  }
  const logout = () => {
    setToken(null); setUser(null); localStorage.removeItem('ut_token'); navigate('home')
    toast.success('Logged out')
  }
  const changeLang = (l) => { setLang(l); localStorage.setItem('ut_lang', l) }

  const ctx = { route, routeParam, navigate, token, user, setUser, setAuth, logout, lang, changeLang, t, refreshUser }

  if (!ready) {
    return <div className="min-h-screen flex items-center justify-center bg-white"><Loader2 className="h-8 w-8 animate-spin text-blue-600" /></div>
  }

  const authPages = ['login', 'register', 'forgot']
  const isAuthPage = authPages.includes(route)

  return (
    <div className="min-h-screen bg-white text-slate-900 flex flex-col">
      <Toaster position="top-center" richColors />
      {!isAuthPage && <Navbar {...ctx} />}
      <main className="flex-1">
        {route === 'home' && <Home {...ctx} />}
        {route === 'imei' && <Checker {...ctx} kind="imei" />}
        {route === 'serial' && <Checker {...ctx} kind="serial" />}
        {route === 'pricing' && <Pricing {...ctx} />}
        {route === 'login' && <AuthPage {...ctx} mode="login" />}
        {route === 'register' && <AuthPage {...ctx} mode="register" />}
        {route === 'forgot' && <ForgotPassword {...ctx} />}
        {route === 'dashboard' && <Dashboard {...ctx} />}
        {route === 'profile' && <Profile {...ctx} />}
        {route === 'contact' && <Contact {...ctx} />}
        {route === 'faq' && <FAQPage {...ctx} />}
        {route === 'terms' && <LegalPage {...ctx} kind="terms" />}
        {route === 'privacy' && <LegalPage {...ctx} kind="privacy" />}
        {route === 'admin' && <AdminDashboard {...ctx} />}
      </main>
      {!isAuthPage && <Footer {...ctx} />}
    </div>
  )
}

// ==================================================================
// Navbar
// ==================================================================
function Navbar({ navigate, route, user, logout, lang, changeLang, t }) {
  const [open, setOpen] = useState(false)
  const links = [
    ['home', t('nav_home')], ['imei', t('nav_imei')], ['serial', t('nav_serial')],
    ['pricing', t('nav_pricing')], ['faq', t('nav_faq')], ['contact', t('nav_contact')],
  ]
  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-100 bg-white/80 backdrop-blur-xl">
      <div className="container flex h-16 items-center justify-between">
        <button onClick={() => navigate('home')} className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 to-blue-400 text-white shadow-lg shadow-blue-500/30">
            <ScanLine className="h-5 w-5" />
          </div>
          <span className="text-lg font-bold tracking-tight">Unlock<span className="text-blue-600">Tap</span></span>
        </button>

        <nav className="hidden items-center gap-1 lg:flex">
          {links.map(([r, label]) => (
            <button key={r} onClick={() => navigate(r)}
              className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${route === r ? 'bg-blue-50 text-blue-700' : 'text-slate-600 hover:text-blue-700'}`}>
              {label}
            </button>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <Select value={lang} onValueChange={changeLang}>
            <SelectTrigger className="hidden h-9 w-[92px] rounded-full border-slate-200 text-xs sm:flex">
              <Globe className="mr-1 h-3.5 w-3.5" /><SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="en">English</SelectItem>
              <SelectItem value="fr">Français</SelectItem>
              <SelectItem value="ht">Kreyòl</SelectItem>
            </SelectContent>
          </Select>

          {user ? (
            <div className="hidden items-center gap-2 md:flex">
              <Badge variant="secondary" className="rounded-full bg-blue-50 text-blue-700 hover:bg-blue-50">
                <CreditCard className="mr-1 h-3.5 w-3.5" />{user.credits} {t('credits')}
              </Badge>
              {user.role === 'admin' && (
                <Button variant="ghost" size="sm" className="rounded-full" onClick={() => navigate('admin')}>{t('admin')}</Button>
              )}
              <Button variant="ghost" size="sm" className="rounded-full" onClick={() => navigate('dashboard')}>
                <LayoutDashboard className="mr-1 h-4 w-4" />{t('dashboard')}
              </Button>
              <button onClick={() => navigate('profile')}>
                <Avatar className="h-9 w-9 border border-slate-200"><AvatarFallback className="bg-blue-600 text-xs text-white">{user.name?.slice(0, 2).toUpperCase()}</AvatarFallback></Avatar>
              </button>
              <Button variant="ghost" size="icon" className="rounded-full" onClick={logout}><LogOut className="h-4 w-4" /></Button>
            </div>
          ) : (
            <div className="hidden items-center gap-2 md:flex">
              <Button variant="ghost" size="sm" className="rounded-full" onClick={() => navigate('login')}>{t('login')}</Button>
              <Button size="sm" className="rounded-full bg-blue-600 hover:bg-blue-700" onClick={() => navigate('register')}>{t('register')}</Button>
            </div>
          )}
          <Button variant="ghost" size="icon" className="lg:hidden" onClick={() => setOpen(!open)}>
            {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>
        </div>
      </div>

      {open && (
        <div className="border-t border-slate-100 bg-white px-4 py-3 lg:hidden">
          <div className="flex flex-col gap-1">
            {links.map(([r, label]) => (
              <button key={r} onClick={() => { navigate(r); setOpen(false) }} className="rounded-lg px-3 py-2 text-left text-sm font-medium text-slate-700 hover:bg-slate-50">{label}</button>
            ))}
            <Separator className="my-2" />
            {user ? (
              <>
                <div className="px-3 py-1 text-sm text-blue-700">{user.credits} {t('credits')}</div>
                <button onClick={() => { navigate('dashboard'); setOpen(false) }} className="rounded-lg px-3 py-2 text-left text-sm">{t('dashboard')}</button>
                <button onClick={() => { navigate('profile'); setOpen(false) }} className="rounded-lg px-3 py-2 text-left text-sm">{t('profile')}</button>
                {user.role === 'admin' && <button onClick={() => { navigate('admin'); setOpen(false) }} className="rounded-lg px-3 py-2 text-left text-sm">{t('admin')}</button>}
                <button onClick={() => { logout(); setOpen(false) }} className="rounded-lg px-3 py-2 text-left text-sm text-red-600">{t('logout')}</button>
              </>
            ) : (
              <>
                <button onClick={() => { navigate('login'); setOpen(false) }} className="rounded-lg px-3 py-2 text-left text-sm">{t('login')}</button>
                <button onClick={() => { navigate('register'); setOpen(false) }} className="rounded-lg px-3 py-2 text-left text-sm font-semibold text-blue-600">{t('register')}</button>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  )
}

// ==================================================================
// Home
// ==================================================================
function Home(props) {
  const { navigate, t } = props
  const features = [
    { icon: Fingerprint, title: 'iCloud & Activation Lock', desc: 'Instantly detect Find My iPhone and Activation Lock status before you buy.' },
    { icon: ShieldCheck, title: 'Blacklist Check', desc: 'Verify if a device has been reported lost, stolen or blacklisted.' },
    { icon: BadgeCheck, title: 'Warranty & Coverage', desc: 'AppleCare eligibility, warranty status and estimated purchase date.' },
    { icon: Cpu, title: 'Full Specs', desc: 'Model, capacity, color, carrier, SIM-lock and country of origin.' },
    { icon: Zap, title: 'Instant Results', desc: 'Reports generated in seconds from our verification engine.' },
    { icon: Globe, title: 'Multi-language', desc: 'Available in English, French and Haitian Creole.' },
  ]
  return (
    <div>
      {/* Hero */}
      <section className="relative overflow-hidden bg-gradient-to-b from-blue-50/60 via-white to-white">
        <div className="pointer-events-none absolute -top-24 -right-24 h-96 w-96 rounded-full bg-blue-200/40 blur-3xl" />
        <div className="container grid items-center gap-12 py-16 lg:grid-cols-2 lg:py-24">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
            <Badge className="mb-5 rounded-full border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-50"><Sparkles className="mr-1 h-3.5 w-3.5" />{t('hero_badge')}</Badge>
            <h1 className="text-4xl font-bold leading-tight tracking-tight text-slate-900 sm:text-5xl lg:text-6xl">{t('hero_title')}</h1>
            <p className="mt-5 max-w-xl text-lg text-slate-600">{t('hero_sub')}</p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Button size="lg" className="rounded-full bg-blue-600 px-7 hover:bg-blue-700" onClick={() => navigate('imei')}>
                <Smartphone className="mr-2 h-5 w-5" />{t('hero_cta1')}
              </Button>
              <Button size="lg" variant="outline" className="rounded-full border-slate-300 px-7" onClick={() => navigate('serial')}>
                <Apple className="mr-2 h-5 w-5" />{t('hero_cta2')}
              </Button>
            </div>
            <div className="mt-8 flex items-center gap-6 text-sm text-slate-500">
              <div className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-blue-600" />Free preview</div>
              <div className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-blue-600" />No expiry credits</div>
              <div className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-blue-600" />Instant</div>
            </div>
          </motion.div>
          <motion.div initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.6 }} className="relative">
            <div className="overflow-hidden rounded-3xl border border-slate-200 shadow-2xl shadow-blue-500/10">
              <img src={HERO_IMG} alt="Apple device verification" className="h-[420px] w-full object-cover" />
            </div>
            <div className="absolute -bottom-5 -left-5 rounded-2xl border border-slate-100 bg-white p-4 shadow-xl">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-green-100"><CheckCircle2 className="h-5 w-5 text-green-600" /></div>
                <div><p className="text-xs text-slate-500">iCloud Status</p><p className="text-sm font-semibold text-green-600">Clean</p></div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section className="container py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">{t('features_title')}</h2>
          <p className="mt-3 text-slate-600">{t('features_sub')}</p>
        </div>
        <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((f, i) => (
            <motion.div key={i} initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.05 }}>
              <Card className="h-full rounded-2xl border-slate-100 transition-shadow hover:shadow-lg hover:shadow-blue-500/5">
                <CardContent className="p-6">
                  <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-blue-50 text-blue-600"><f.icon className="h-6 w-6" /></div>
                  <h3 className="text-lg font-semibold">{f.title}</h3>
                  <p className="mt-2 text-sm text-slate-600">{f.desc}</p>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      </section>

      {/* How it works / CTA image */}
      <section className="bg-slate-50 py-20">
        <div className="container grid items-center gap-12 lg:grid-cols-2">
          <div className="overflow-hidden rounded-3xl border border-slate-200 shadow-xl">
            <img src={CTA_IMG} alt="Apple branding" className="h-[360px] w-full object-cover" />
          </div>
          <div>
            <h2 className="text-3xl font-bold tracking-tight">How it works</h2>
            <div className="mt-8 space-y-6">
              {[
                ['Enter IMEI or Serial', 'Type the 15-digit IMEI or Apple serial number.'],
                ['Get a free preview', 'Instantly see brand, model, capacity and color.'],
                ['Unlock full report', 'Spend 1 credit to reveal iCloud, blacklist, warranty & more.'],
              ].map(([title, desc], i) => (
                <div key={i} className="flex gap-4">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-blue-600 text-sm font-bold text-white">{i + 1}</div>
                  <div><h4 className="font-semibold">{title}</h4><p className="text-sm text-slate-600">{desc}</p></div>
                </div>
              ))}
            </div>
            <Button className="mt-8 rounded-full bg-blue-600 hover:bg-blue-700" onClick={() => navigate('imei')}>{t('check_now')} <ChevronRight className="ml-1 h-4 w-4" /></Button>
          </div>
        </div>
      </section>

      {/* Pricing preview */}
      <PricingPreview {...props} />

      {/* Testimonials */}
      <section className="container py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">{t('testi_title')}</h2>
        </div>
        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {[
            ['Marc D.', 'Phone Reseller', 'UnlockTap saved me from buying 3 iCloud-locked iPhones. The blacklist check is a lifesaver.'],
            ['Sophie L.', 'Repair Shop Owner', 'Fast, accurate and the credit system is perfect for my daily volume. Highly recommend.'],
            ['Jean B.', 'Independent Technician', 'The serial checker gives me warranty info instantly. Multi-language support is a huge plus.'],
          ].map(([name, role, quote], i) => (
            <Card key={i} className="rounded-2xl border-slate-100">
              <CardContent className="p-6">
                <div className="mb-3 flex gap-0.5">{[...Array(5)].map((_, j) => <Star key={j} className="h-4 w-4 fill-yellow-400 text-yellow-400" />)}</div>
                <p className="text-slate-700">“{quote}”</p>
                <div className="mt-5 flex items-center gap-3">
                  <Avatar className="h-10 w-10"><AvatarFallback className="bg-blue-600 text-white">{name.slice(0, 1)}</AvatarFallback></Avatar>
                  <div><p className="text-sm font-semibold">{name}</p><p className="text-xs text-slate-500">{role}</p></div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* FAQ */}
      <section className="bg-slate-50 py-20">
        <div className="container max-w-3xl">
          <h2 className="mb-8 text-center text-3xl font-bold tracking-tight">{t('faq_title')}</h2>
          <FAQAccordion />
        </div>
      </section>
    </div>
  )
}

const FAQ_ITEMS = [
  ['What is an IMEI number?', 'The IMEI (International Mobile Equipment Identity) is a unique 15-digit number that identifies your device. Dial *#06# on any phone to see it.'],
  ['Where do I find my Apple serial number?', 'Go to Settings > General > About on iOS, or click the Apple menu > About This Mac. It is also printed on the device or its box.'],
  ['What does the free preview show?', 'The free preview shows the brand, model, capacity and color of the device. Premium fields like iCloud lock, blacklist and warranty require 1 credit.'],
  ['Do credits expire?', 'No. Credits never expire and can be used any time for either IMEI or serial checks.'],
  ['Is the data real?', 'This demo uses a realistic mock verification engine. Production API providers can be connected via secure environment variables.'],
  ['Which payment methods do you accept?', 'This demo uses a mock payment system so you can test the full flow instantly. Real gateways can be integrated later.'],
]
function FAQAccordion() {
  return (
    <Accordion type="single" collapsible className="w-full">
      {FAQ_ITEMS.map(([q, a], i) => (
        <AccordionItem key={i} value={`item-${i}`} className="rounded-xl border border-slate-100 bg-white px-4 mb-3">
          <AccordionTrigger className="text-left text-sm font-semibold hover:no-underline">{q}</AccordionTrigger>
          <AccordionContent className="text-sm text-slate-600">{a}</AccordionContent>
        </AccordionItem>
      ))}
    </Accordion>
  )
}

// ==================================================================
// Pricing
// ==================================================================
function usePlans() {
  const [plans, setPlans] = useState([])
  useEffect(() => { api('/plans').then(d => setPlans(d.plans)).catch(() => {}) }, [])
  return plans
}

function PlanCard({ plan, onBuy, t, cta }) {
  return (
    <Card className={`relative flex flex-col rounded-2xl ${plan.popular ? 'border-2 border-blue-600 shadow-xl shadow-blue-500/10' : 'border-slate-100'}`}>
      {plan.popular && <Badge className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-blue-600 hover:bg-blue-600">{t('most_popular')}</Badge>}
      <CardHeader>
        <CardTitle className="text-lg">{plan.name}</CardTitle>
        <div className="flex items-end gap-1"><span className="text-4xl font-bold">${plan.price}</span></div>
        <CardDescription>{plan.credits} credit{plan.credits > 1 ? 's' : ''}</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-1 flex-col">
        <ul className="mb-6 space-y-2 text-sm">
          {(plan.features || []).map((f, i) => (
            <li key={i} className="flex items-center gap-2 text-slate-600"><CheckCircle2 className="h-4 w-4 shrink-0 text-blue-600" />{f}</li>
          ))}
        </ul>
        <Button className={`mt-auto w-full rounded-full ${plan.popular ? 'bg-blue-600 hover:bg-blue-700' : ''}`} variant={plan.popular ? 'default' : 'outline'} onClick={() => onBuy(plan)}>
          {cta}
        </Button>
      </CardContent>
    </Card>
  )
}

function PricingPreview(props) {
  const { navigate, t } = props
  const plans = usePlans()
  return (
    <section className="container py-20">
      <div className="mx-auto max-w-2xl text-center">
        <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">{t('pricing_title')}</h2>
        <p className="mt-3 text-slate-600">{t('pricing_sub')}</p>
      </div>
      <div className="mt-12 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {plans.map(p => <PlanCard key={p.id} plan={p} t={t} cta={t('get_started')} onBuy={() => navigate('pricing')} />)}
      </div>
    </section>
  )
}

function Pricing(props) {
  const { user, token, setUser, navigate, t } = props
  const plans = usePlans()
  const [loading, setLoading] = useState(null)

  const buy = async (plan) => {
    if (!user) { toast.info('Please log in to purchase credits'); navigate('login'); return }
    setLoading(plan.id)
    try {
      const res = await api('/checkout', { method: 'POST', token, body: { planId: plan.id } })
      setUser({ ...user, credits: res.credits })
      toast.success(res.message)
      navigate('dashboard')
    } catch (e) { toast.error(e.message) } finally { setLoading(null) }
  }

  return (
    <div className="container py-16">
      <div className="mx-auto max-w-2xl text-center">
        <Badge className="mb-4 rounded-full border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-50"><CreditCard className="mr-1 h-3.5 w-3.5" />Credits</Badge>
        <h1 className="text-4xl font-bold tracking-tight">{t('pricing_title')}</h1>
        <p className="mt-3 text-slate-600">{t('pricing_sub')} A demo (mock) payment is used — no real card required.</p>
      </div>
      <div className="mt-12 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {plans.map(p => (
          <PlanCard key={p.id} plan={p} t={t} cta={loading === p.id ? '...' : t('buy_credits')} onBuy={buy} />
        ))}
      </div>
    </div>
  )
}

// ==================================================================
// Checker (IMEI / Serial)
// ==================================================================
function Checker({ kind, navigate, token, user, setUser, t }) {
  const [value, setValue] = useState('')
  const [result, setResult] = useState(null)
  const [premium, setPremium] = useState(null)
  const [loading, setLoading] = useState(false)
  const [unlocking, setUnlocking] = useState(false)

  const isImei = kind === 'imei'
  const title = isImei ? t('nav_imei') : t('nav_serial')
  const placeholder = isImei ? t('enter_imei') : t('enter_serial')

  const runCheck = async () => {
    setResult(null); setPremium(null)
    const clean = isImei ? value.replace(/\s|-/g, '') : value.trim().toUpperCase()
    setLoading(true)
    try {
      const res = await api(isImei ? '/imei/check' : '/serial/check', {
        method: 'POST', token, body: isImei ? { imei: clean } : { serial: clean },
      })
      setResult(res)
    } catch (e) { toast.error(e.message) } finally { setLoading(false) }
  }

  const unlock = async () => {
    if (!user) { toast.info('Log in to unlock the full report'); navigate('login'); return }
    setUnlocking(true)
    try {
      const res = await api('/unlock', { method: 'POST', token, body: { searchId: result.searchId } })
      setPremium(res.premium)
      setUser({ ...user, credits: res.credits })
      toast.success('Full report unlocked')
    } catch (e) {
      if (e.data?.code === 'NO_CREDITS') { toast.error('Not enough credits'); navigate('pricing') }
      else toast.error(e.message)
    } finally { setUnlocking(false) }
  }

  return (
    <div className="bg-gradient-to-b from-blue-50/40 to-white">
      <div className="container max-w-3xl py-16">
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-600 text-white shadow-lg shadow-blue-500/30">
            {isImei ? <Smartphone className="h-7 w-7" /> : <Apple className="h-7 w-7" />}
          </div>
          <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">{title}</h1>
          <p className="mt-2 text-slate-600">{isImei ? 'Enter a 15-digit IMEI to verify an Apple device.' : 'Enter an Apple serial number to verify warranty & coverage.'}</p>
        </div>

        <Card className="mt-8 rounded-2xl border-slate-100 shadow-lg shadow-blue-500/5">
          <CardContent className="p-6">
            <Label className="mb-2 block text-sm font-medium">{placeholder}</Label>
            <div className="flex flex-col gap-3 sm:flex-row">
              <Input value={value} onChange={e => setValue(e.target.value)} placeholder={isImei ? '359876543210987' : 'C39XY0ABJCLF'}
                className="h-12 rounded-xl text-base" onKeyDown={e => e.key === 'Enter' && runCheck()} maxLength={isImei ? 17 : 14} />
              <Button className="h-12 rounded-xl bg-blue-600 px-8 hover:bg-blue-700" onClick={runCheck} disabled={loading}>
                {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <><Search className="mr-2 h-5 w-5" />{t('check_now')}</>}
              </Button>
            </div>
            {isImei && <p className="mt-2 text-xs text-slate-400">Tip: dial *#06# on the device to view its IMEI.</p>}
          </CardContent>
        </Card>

        {result && (
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="mt-8 space-y-6">
            {/* Free preview */}
            <Card className="rounded-2xl border-slate-100">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
                <CardTitle className="text-base">{t('free_preview')}</CardTitle>
                <Badge variant="secondary" className="rounded-full bg-green-50 text-green-700 hover:bg-green-50">Free</Badge>
              </CardHeader>
              <CardContent>
                <dl className="grid gap-x-8 gap-y-3 sm:grid-cols-2">
                  {Object.entries(result.free).map(([k, v]) => (
                    <div key={k} className="flex justify-between border-b border-slate-50 py-1.5 text-sm">
                      <dt className="text-slate-500">{k}</dt><dd className="font-medium text-slate-900">{v}</dd>
                    </div>
                  ))}
                </dl>
              </CardContent>
            </Card>

            {/* Premium */}
            <Card className="rounded-2xl border-blue-100">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
                <CardTitle className="flex items-center gap-2 text-base"><Lock className="h-4 w-4 text-blue-600" />{t('premium_report')}</CardTitle>
                <Badge className="rounded-full bg-blue-600 hover:bg-blue-600">Premium</Badge>
              </CardHeader>
              <CardContent>
                {premium ? (
                  <dl className="grid gap-x-8 gap-y-3 sm:grid-cols-2">
                    {Object.entries(premium).map(([k, v]) => {
                      const bad = /blacklist/i.test(k) ? /clean/i.test(v) : /find my|icloud/i.test(k) ? /clean|off/i.test(v) : true
                      const isStatus = /status|find my|icloud|lock/i.test(k)
                      return (
                        <div key={k} className="flex items-center justify-between border-b border-slate-50 py-1.5 text-sm">
                          <dt className="text-slate-500">{k}</dt>
                          <dd className={`font-medium ${isStatus ? (bad ? 'text-green-600' : 'text-red-600') : 'text-slate-900'} flex items-center gap-1`}>
                            {isStatus && (bad ? <CheckCircle2 className="h-3.5 w-3.5" /> : <XCircle className="h-3.5 w-3.5" />)}{v}
                          </dd>
                        </div>
                      )
                    })}
                  </dl>
                ) : (
                  <div className="relative">
                    <div className="grid gap-x-8 gap-y-3 blur-sm select-none sm:grid-cols-2" aria-hidden>
                      {['Find My iPhone', 'iCloud Status', 'Blacklist Status', 'Warranty Status', 'Carrier', 'SIM-Lock Status'].map(k => (
                        <div key={k} className="flex justify-between border-b border-slate-50 py-1.5 text-sm"><span className="text-slate-500">{k}</span><span className="font-medium">••••••</span></div>
                      ))}
                    </div>
                    <div className="absolute inset-0 flex flex-col items-center justify-center gap-3">
                      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-600 text-white shadow-lg"><Lock className="h-5 w-5" /></div>
                      <Button className="rounded-full bg-blue-600 hover:bg-blue-700" onClick={unlock} disabled={unlocking}>
                        {unlocking ? <Loader2 className="h-4 w-4 animate-spin" /> : t('unlock_report')}
                      </Button>
                      {user && <p className="text-xs text-slate-500">You have {user.credits} credit(s)</p>}
                      {!user && <button onClick={() => navigate('login')} className="text-xs text-blue-600 underline">Log in to unlock</button>}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        )}
      </div>
    </div>
  )
}

// ==================================================================
// Auth Pages
// ==================================================================
function AuthShell({ title, sub, children, footer, wide, onHome }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-600 via-blue-500 to-blue-400 p-4">
      <div className={`w-full ${wide ? 'max-w-lg' : 'max-w-md'}`}>
        <button onClick={onHome} className="mb-6 flex items-center justify-center gap-2 text-white">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/20 backdrop-blur"><ScanLine className="h-5 w-5" /></div>
          <span className="text-xl font-bold">Unlock<span className="text-blue-100">Tap</span></span>
        </button>
        <Card className="rounded-2xl border-0 shadow-2xl">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl">{title}</CardTitle>
            <CardDescription>{sub}</CardDescription>
          </CardHeader>
          <CardContent>{children}</CardContent>
        </Card>
        <div className="mt-4 text-center text-sm text-white/90">{footer}</div>
      </div>
    </div>
  )
}

function AuthPage({ mode, navigate, setAuth, t }) {
  const isLogin = mode === 'login'
  const [form, setForm] = useState({ name: '', username: '', country: '', phone: '', email: '', password: '', confirmPassword: '' })
  const [loading, setLoading] = useState(false)
  const upd = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    if (!isLogin) {
      if (!form.country) { toast.error('Please select your country'); return }
      if (form.password !== form.confirmPassword) { toast.error('Passwords do not match'); return }
    }
    setLoading(true)
    try {
      const payload = isLogin
        ? { email: form.email, password: form.password }
        : { name: form.name, username: form.username, country: form.country, phone: form.phone, email: form.email, password: form.password }
      const res = await api(isLogin ? '/auth/login' : '/auth/register', { method: 'POST', body: payload })
      setAuth(res.token, res.user)
      toast.success(isLogin ? 'Welcome back!' : 'Account created! You got 3 free credits.')
      navigate(res.user.role === 'admin' ? 'admin' : 'dashboard')
    } catch (err) { toast.error(err.message) } finally { setLoading(false) }
  }

  const inputCls = 'mt-1 h-11 rounded-xl'

  return (
    <AuthShell
      wide={!isLogin}
      onHome={() => navigate('home')}
      title={isLogin ? t('welcome_back') : t('create_account')}
      sub={isLogin ? t('signin_sub') : t('register_sub')}
      footer={
        <button onClick={() => navigate(isLogin ? 'register' : 'login')} className="underline">
          {isLogin ? `${t('no_account')} ${t('register')}` : `${t('have_account')} ${t('login')}`}
        </button>
      }
    >
      {isLogin ? (
        <form onSubmit={submit} className="space-y-4">
          <div><Label>Email Address</Label><Input type="email" className={inputCls} value={form.email} onChange={upd('email')} required /></div>
          <div><Label>Password</Label><Input type="password" className={inputCls} value={form.password} onChange={upd('password')} required /></div>
          <div className="text-right"><button type="button" onClick={() => navigate('forgot')} className="text-sm text-blue-600 hover:underline">{t('forgot')}</button></div>
          <Button type="submit" className="h-11 w-full rounded-xl bg-blue-600 hover:bg-blue-700" disabled={loading}>
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : t('login')}
          </Button>
          <p className="rounded-lg bg-slate-50 p-2 text-center text-xs text-slate-500">Admin demo: admin@unlocktap.com / Admin@123</p>
        </form>
      ) : (
        <form onSubmit={submit} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div><Label>Full Name</Label><Input className={inputCls} value={form.name} onChange={upd('name')} placeholder="John Smith" required /></div>
            <div><Label>Username</Label><Input className={inputCls} value={form.username} onChange={upd('username')} placeholder="johnsmith" required /></div>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <Label>Country</Label>
              <Select value={form.country} onValueChange={(v) => setForm({ ...form, country: v })}>
                <SelectTrigger className={inputCls}><SelectValue placeholder="Select country" /></SelectTrigger>
                <SelectContent className="max-h-64">
                  {COUNTRIES_LIST.map(c => <SelectItem key={c} value={c}>{c}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div><Label>Phone Number</Label><Input type="tel" className={inputCls} value={form.phone} onChange={upd('phone')} placeholder="+1 555 123 4567" required /></div>
          </div>
          <div><Label>Email Address</Label><Input type="email" className={inputCls} value={form.email} onChange={upd('email')} placeholder="john@example.com" required /></div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div><Label>Password</Label><Input type="password" className={inputCls} value={form.password} onChange={upd('password')} required /></div>
            <div><Label>Confirm Password</Label><Input type="password" className={inputCls} value={form.confirmPassword} onChange={upd('confirmPassword')} required /></div>
          </div>
          <Button type="submit" className="h-11 w-full rounded-xl bg-blue-600 hover:bg-blue-700" disabled={loading}>
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : t('register')}
          </Button>
        </form>
      )}
    </AuthShell>
  )
}

function ForgotPassword({ navigate, t }) {
  const [step, setStep] = useState(1)
  const [email, setEmail] = useState('')
  const [code, setCode] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)

  const requestCode = async (e) => {
    e.preventDefault(); setLoading(true)
    try {
      const res = await api('/auth/forgot-password', { method: 'POST', body: { email } })
      if (res.demoResetCode) { setCode(res.demoResetCode); toast.success(`Demo reset code: ${res.demoResetCode}`) }
      else toast.success(res.message)
      setStep(2)
    } catch (err) { toast.error(err.message) } finally { setLoading(false) }
  }
  const reset = async (e) => {
    e.preventDefault(); setLoading(true)
    try {
      const res = await api('/auth/reset-password', { method: 'POST', body: { email, code, password } })
      toast.success(res.message); navigate('login')
    } catch (err) { toast.error(err.message) } finally { setLoading(false) }
  }

  return (
    <AuthShell title="Reset password" sub={step === 1 ? 'Enter your email to receive a reset code' : 'Enter the code and your new password'}
      footer={<button onClick={() => navigate('login')} className="underline">Back to {t('login')}</button>}>
      {step === 1 ? (
        <form onSubmit={requestCode} className="space-y-4">
          <div><Label>{t('email')}</Label><Input type="email" className="mt-1 h-11 rounded-xl" value={email} onChange={e => setEmail(e.target.value)} required /></div>
          <Button className="h-11 w-full rounded-xl bg-blue-600 hover:bg-blue-700" disabled={loading}>{loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Send reset code'}</Button>
        </form>
      ) : (
        <form onSubmit={reset} className="space-y-4">
          <div><Label>Reset code</Label><Input className="mt-1 h-11 rounded-xl" value={code} onChange={e => setCode(e.target.value)} required /></div>
          <div><Label>New {t('password')}</Label><Input type="password" className="mt-1 h-11 rounded-xl" value={password} onChange={e => setPassword(e.target.value)} required /></div>
          <Button className="h-11 w-full rounded-xl bg-blue-600 hover:bg-blue-700" disabled={loading}>{loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Reset password'}</Button>
        </form>
      )}
    </AuthShell>
  )
}

// ==================================================================
// Dashboard
// ==================================================================
function Protected({ user, navigate, children }) {
  useEffect(() => { if (!user) navigate('login') }, [user, navigate])
  if (!user) return <div className="container py-20 text-center text-slate-500">Redirecting to login...</div>
  return children
}

function Dashboard(props) {
  const { user, token, navigate, t } = props
  const [data, setData] = useState(null)
  const [history, setHistory] = useState([])
  const [orders, setOrders] = useState([])
  const [reports, setReports] = useState([])

  useEffect(() => {
    if (!token) return
    api('/dashboard', { token }).then(setData).catch(() => {})
    api('/history', { token }).then(d => setHistory(d.items)).catch(() => {})
    api('/orders', { token }).then(d => setOrders(d.items)).catch(() => {})
    api('/reports', { token }).then(d => setReports(d.items)).catch(() => {})
  }, [token])

  return (
    <Protected user={user} navigate={navigate}>
      <div className="container py-12">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{t('welcome_back')}, {user?.name?.split(' ')[0]}</h1>
            <p className="text-slate-500">{user?.email}</p>
          </div>
          <Button className="rounded-full bg-blue-600 hover:bg-blue-700" onClick={() => navigate('pricing')}><CreditCard className="mr-2 h-4 w-4" />{t('buy_credits')}</Button>
        </div>

        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard icon={CreditCard} label={t('credits')} value={data?.stats.credits ?? user?.credits} accent />
          <StatCard icon={Search} label={t('search_history')} value={data?.stats.searches ?? 0} />
          <StatCard icon={FileText} label={t('reports')} value={data?.stats.reports ?? 0} />
          <StatCard icon={CreditCard} label={t('orders')} value={data?.stats.orders ?? 0} />
        </div>

        <Tabs defaultValue="history" className="mt-10">
          <TabsList className="rounded-full">
            <TabsTrigger value="history" className="rounded-full">{t('search_history')}</TabsTrigger>
            <TabsTrigger value="reports" className="rounded-full">{t('reports')}</TabsTrigger>
            <TabsTrigger value="orders" className="rounded-full">{t('orders')}</TabsTrigger>
          </TabsList>

          <TabsContent value="history" className="mt-6">
            <DataCard empty={history.length === 0} emptyText="No searches yet.">
              <Table>
                <TableHeader><TableRow><TableHead>Type</TableHead><TableHead>Query</TableHead><TableHead>Model</TableHead><TableHead>Status</TableHead><TableHead>Date</TableHead></TableRow></TableHeader>
                <TableBody>
                  {history.map(h => (
                    <TableRow key={h.id}>
                      <TableCell><Badge variant="secondary" className="uppercase">{h.type}</Badge></TableCell>
                      <TableCell className="font-mono text-xs">{h.query}</TableCell>
                      <TableCell>{h.model}</TableCell>
                      <TableCell>{h.unlocked ? <Badge className="bg-green-600 hover:bg-green-600">Unlocked</Badge> : <Badge variant="outline">Preview</Badge>}</TableCell>
                      <TableCell className="text-xs text-slate-500">{new Date(h.createdAt).toLocaleString()}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </DataCard>
          </TabsContent>

          <TabsContent value="reports" className="mt-6">
            <DataCard empty={reports.length === 0} emptyText="No unlocked reports yet.">
              <div className="grid gap-4 md:grid-cols-2">
                {reports.map(r => (
                  <Card key={r.id} className="rounded-xl border-slate-100">
                    <CardHeader className="pb-2"><div className="flex items-center justify-between"><CardTitle className="text-base">{r.model}</CardTitle><Badge variant="secondary" className="uppercase">{r.type}</Badge></div><CardDescription className="font-mono text-xs">{r.query}</CardDescription></CardHeader>
                    <CardContent className="space-y-1 text-xs">
                      {Object.entries(r.data).slice(0, 6).map(([k, v]) => <div key={k} className="flex justify-between border-b border-slate-50 py-1"><span className="text-slate-500">{k}</span><span className="font-medium">{v}</span></div>)}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </DataCard>
          </TabsContent>

          <TabsContent value="orders" className="mt-6">
            <DataCard empty={orders.length === 0} emptyText="No orders yet.">
              <Table>
                <TableHeader><TableRow><TableHead>Plan</TableHead><TableHead>Credits</TableHead><TableHead>Amount</TableHead><TableHead>Status</TableHead><TableHead>Date</TableHead></TableRow></TableHeader>
                <TableBody>
                  {orders.map(o => (
                    <TableRow key={o.id}>
                      <TableCell className="font-medium">{o.planName}</TableCell>
                      <TableCell>+{o.credits}</TableCell>
                      <TableCell>${o.amount}</TableCell>
                      <TableCell><Badge className="bg-green-600 hover:bg-green-600 capitalize">{o.status}</Badge></TableCell>
                      <TableCell className="text-xs text-slate-500">{new Date(o.createdAt).toLocaleString()}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </DataCard>
          </TabsContent>
        </Tabs>
      </div>
    </Protected>
  )
}

function StatCard({ icon: Icon, label, value, accent }) {
  return (
    <Card className={`rounded-2xl ${accent ? 'border-blue-100 bg-blue-50/50' : 'border-slate-100'}`}>
      <CardContent className="flex items-center gap-4 p-5">
        <div className={`flex h-12 w-12 items-center justify-center rounded-xl ${accent ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-600'}`}><Icon className="h-6 w-6" /></div>
        <div><p className="text-sm text-slate-500">{label}</p><p className="text-2xl font-bold">{value}</p></div>
      </CardContent>
    </Card>
  )
}
function DataCard({ empty, emptyText, children }) {
  return <Card className="rounded-2xl border-slate-100"><CardContent className="p-5">{empty ? <div className="py-12 text-center text-sm text-slate-400">{emptyText}</div> : children}</CardContent></Card>
}

// ==================================================================
// Profile
// ==================================================================
function Profile(props) {
  const { user, token, setUser, navigate, lang, changeLang, t } = props
  const [name, setName] = useState(user?.name || '')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)

  const save = async () => {
    setLoading(true)
    try {
      const body = { name, language: lang }
      if (password) body.password = password
      const res = await api('/profile', { method: 'PUT', token, body })
      setUser(res.user); setPassword(''); toast.success('Profile updated')
    } catch (e) { toast.error(e.message) } finally { setLoading(false) }
  }

  return (
    <Protected user={user} navigate={navigate}>
      <div className="container max-w-2xl py-12">
        <h1 className="text-3xl font-bold tracking-tight">{t('profile')}</h1>
        <Card className="mt-8 rounded-2xl border-slate-100">
          <CardContent className="space-y-5 p-6">
            <div className="flex items-center gap-4">
              <Avatar className="h-16 w-16"><AvatarFallback className="bg-blue-600 text-lg text-white">{user?.name?.slice(0, 2).toUpperCase()}</AvatarFallback></Avatar>
              <div><p className="font-semibold">{user?.name}</p><p className="text-sm text-slate-500">{user?.email}</p><Badge className="mt-1 bg-blue-50 text-blue-700 hover:bg-blue-50" variant="secondary">{user?.credits} {t('credits')}</Badge></div>
            </div>
            <Separator />
            <div className="grid gap-4 sm:grid-cols-3">
              <div><Label className="text-xs text-slate-500">Username</Label><p className="mt-1 text-sm font-medium">{user?.username || '—'}</p></div>
              <div><Label className="text-xs text-slate-500">Country</Label><p className="mt-1 text-sm font-medium">{user?.country || '—'}</p></div>
              <div><Label className="text-xs text-slate-500">Phone</Label><p className="mt-1 text-sm font-medium">{user?.phone || '—'}</p></div>
            </div>
            <Separator />
            <div><Label>{t('name')}</Label><Input className="mt-1 h-11 rounded-xl" value={name} onChange={e => setName(e.target.value)} /></div>
            <div><Label>{t('email')}</Label><Input className="mt-1 h-11 rounded-xl bg-slate-50" value={user?.email} disabled /></div>
            <div><Label>{t('language')}</Label>
              <Select value={lang} onValueChange={changeLang}>
                <SelectTrigger className="mt-1 h-11 rounded-xl"><SelectValue /></SelectTrigger>
                <SelectContent><SelectItem value="en">English</SelectItem><SelectItem value="fr">Français</SelectItem><SelectItem value="ht">Kreyòl Ayisyen</SelectItem></SelectContent>
              </Select>
            </div>
            <div><Label>New {t('password')} (optional)</Label><Input type="password" className="mt-1 h-11 rounded-xl" value={password} onChange={e => setPassword(e.target.value)} placeholder="Leave blank to keep current" /></div>
            <Button className="rounded-full bg-blue-600 hover:bg-blue-700" onClick={save} disabled={loading}>{loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Save changes'}</Button>
          </CardContent>
        </Card>
      </div>
    </Protected>
  )
}

// ==================================================================
// Contact / FAQ / Legal
// ==================================================================
function Contact({ t }) {
  const [form, setForm] = useState({ name: '', email: '', message: '' })
  const [loading, setLoading] = useState(false)
  const submit = async (e) => {
    e.preventDefault(); setLoading(true)
    try { const res = await api('/contact', { method: 'POST', body: form }); toast.success(res.message); setForm({ name: '', email: '', message: '' }) }
    catch (err) { toast.error(err.message) } finally { setLoading(false) }
  }
  return (
    <div className="container max-w-xl py-16">
      <div className="text-center"><h1 className="text-3xl font-bold tracking-tight">{t('contact_title')}</h1><p className="mt-2 text-slate-600">{t('contact_sub')}</p></div>
      <Card className="mt-8 rounded-2xl border-slate-100">
        <CardContent className="p-6">
          <form onSubmit={submit} className="space-y-4">
            <div><Label>{t('name')}</Label><Input className="mt-1 h-11 rounded-xl" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required /></div>
            <div><Label>{t('email')}</Label><Input type="email" className="mt-1 h-11 rounded-xl" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} required /></div>
            <div><Label>Message</Label><Textarea className="mt-1 min-h-32 rounded-xl" value={form.message} onChange={e => setForm({ ...form, message: e.target.value })} required /></div>
            <Button className="w-full rounded-xl bg-blue-600 hover:bg-blue-700" disabled={loading}>{loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <><Mail className="mr-2 h-4 w-4" />{t('send_message')}</>}</Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

function FAQPage({ t }) {
  return (
    <div className="container max-w-3xl py-16">
      <h1 className="mb-8 text-center text-3xl font-bold tracking-tight">{t('faq_title')}</h1>
      <FAQAccordion />
    </div>
  )
}

function LegalPage({ kind }) {
  const isTerms = kind === 'terms'
  return (
    <div className="container max-w-3xl py-16">
      <h1 className="text-3xl font-bold tracking-tight">{isTerms ? 'Terms of Service' : 'Privacy Policy'}</h1>
      <p className="mt-2 text-sm text-slate-500">Last updated: June 2025</p>
      <div className="prose mt-8 space-y-4 text-sm leading-relaxed text-slate-600">
        {isTerms ? (
          <>
            <p>Welcome to UnlockTap. By using our device verification services you agree to these terms. UnlockTap provides IMEI and Apple serial number lookup services for informational purposes.</p>
            <p><strong>1. Use of Service.</strong> Credits purchased are used to unlock premium verification reports. Credits are non-refundable but never expire.</p>
            <p><strong>2. Accuracy.</strong> This demo uses a mock verification engine. Reports are provided "as is" without warranty. In production, data is sourced from third-party providers.</p>
            <p><strong>3. Acceptable Use.</strong> You may not use UnlockTap for any unlawful purpose, including facilitating the trade of stolen devices.</p>
            <p><strong>4. Accounts.</strong> You are responsible for maintaining the confidentiality of your account credentials.</p>
            <p><strong>5. Changes.</strong> We may update these terms at any time. Continued use constitutes acceptance.</p>
          </>
        ) : (
          <>
            <p>Your privacy matters to UnlockTap. This policy explains what we collect and how we use it.</p>
            <p><strong>1. Data We Collect.</strong> Account information (name, email), search history (IMEI/serial queries) and order records.</p>
            <p><strong>2. How We Use It.</strong> To provide verification services, maintain your dashboard and process credit purchases.</p>
            <p><strong>3. Security.</strong> Passwords are hashed. API keys for third-party providers are stored securely in environment variables and never exposed to the client.</p>
            <p><strong>4. Sharing.</strong> We do not sell your data. Queries may be sent to verification providers solely to fulfil your request.</p>
            <p><strong>5. Contact.</strong> For privacy requests, contact us via the Contact page.</p>
          </>
        )}
      </div>
    </div>
  )
}

// ==================================================================
// Admin Dashboard
// ==================================================================
function AdminDashboard(props) {
  const { user, token, navigate, t } = props
  const [stats, setStats] = useState(null)
  const [users, setUsers] = useState([])
  const [searches, setSearches] = useState([])
  const [orders, setOrders] = useState([])
  const [plans, setPlans] = useState([])
  const [contacts, setContacts] = useState([])

  const load = useCallback(() => {
    api('/admin/stats', { token }).then(d => setStats(d.stats)).catch(() => {})
    api('/admin/users', { token }).then(d => setUsers(d.items)).catch(() => {})
    api('/admin/searches', { token }).then(d => setSearches(d.items)).catch(() => {})
    api('/admin/orders', { token }).then(d => setOrders(d.items)).catch(() => {})
    api('/admin/plans', { token }).then(d => setPlans(d.items)).catch(() => {})
    api('/admin/contacts', { token }).then(d => setContacts(d.items)).catch(() => {})
  }, [token])

  useEffect(() => { if (token && user?.role === 'admin') load() }, [token, user, load])

  useEffect(() => { if (user && user.role !== 'admin') navigate('dashboard') }, [user, navigate])

  const updateUser = async (id, body) => {
    try { await api(`/admin/users/${id}`, { method: 'PUT', token, body }); toast.success('User updated'); load() }
    catch (e) { toast.error(e.message) }
  }
  const updatePlan = async (id, body) => {
    try { await api(`/admin/plans/${id}`, { method: 'PUT', token, body }); toast.success('Plan updated'); load() }
    catch (e) { toast.error(e.message) }
  }

  if (!user) return <Protected user={user} navigate={navigate}><div /></Protected>

  return (
    <div className="container py-12">
      <div className="mb-8 flex items-center gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-slate-900 text-white"><Settings className="h-6 w-6" /></div>
        <div><h1 className="text-3xl font-bold tracking-tight">Admin Dashboard</h1><p className="text-slate-500">Manage users, credits, pricing & activity</p></div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-6">
        <StatCard icon={Users} label="Users" value={stats?.users ?? 0} accent />
        <StatCard icon={Search} label="Searches" value={stats?.searches ?? 0} />
        <StatCard icon={FileText} label="Reports" value={stats?.reports ?? 0} />
        <StatCard icon={CreditCard} label="Orders" value={stats?.orders ?? 0} />
        <StatCard icon={DollarSign} label="Revenue" value={`$${stats?.revenue ?? 0}`} />
        <StatCard icon={Mail} label="Messages" value={stats?.contacts ?? 0} />
      </div>

      <Tabs defaultValue="users" className="mt-10">
        <TabsList className="flex-wrap rounded-full">
          <TabsTrigger value="users" className="rounded-full">Users</TabsTrigger>
          <TabsTrigger value="pricing" className="rounded-full">Pricing</TabsTrigger>
          <TabsTrigger value="searches" className="rounded-full">Searches</TabsTrigger>
          <TabsTrigger value="orders" className="rounded-full">Orders</TabsTrigger>
          <TabsTrigger value="messages" className="rounded-full">Messages</TabsTrigger>
        </TabsList>

        <TabsContent value="users" className="mt-6">
          <DataCard empty={users.length === 0} emptyText="No users.">
            <Table>
              <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Email</TableHead><TableHead>Role</TableHead><TableHead>Credits</TableHead><TableHead>Actions</TableHead></TableRow></TableHeader>
              <TableBody>
                {users.map(u => (
                  <TableRow key={u.id}>
                    <TableCell className="font-medium">{u.name}</TableCell>
                    <TableCell className="text-sm text-slate-500">{u.email}</TableCell>
                    <TableCell><Badge variant={u.role === 'admin' ? 'default' : 'secondary'} className={u.role === 'admin' ? 'bg-slate-900' : ''}>{u.role}</Badge>{u.banned && <Badge variant="destructive" className="ml-1">banned</Badge>}</TableCell>
                    <TableCell>{u.credits}</TableCell>
                    <TableCell className="flex flex-wrap gap-1">
                      <Button size="sm" variant="outline" className="h-7 rounded-full text-xs" onClick={() => updateUser(u.id, { credits: (u.credits || 0) + 10 })}>+10 cr</Button>
                      <Button size="sm" variant="outline" className="h-7 rounded-full text-xs" onClick={() => updateUser(u.id, { role: u.role === 'admin' ? 'user' : 'admin' })}>{u.role === 'admin' ? 'Demote' : 'Promote'}</Button>
                      <Button size="sm" variant="outline" className="h-7 rounded-full text-xs" onClick={() => updateUser(u.id, { banned: !u.banned })}>{u.banned ? 'Unban' : 'Ban'}</Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </DataCard>
        </TabsContent>

        <TabsContent value="pricing" className="mt-6">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {plans.map(p => (
              <Card key={p.id} className="rounded-2xl border-slate-100">
                <CardHeader className="pb-2"><CardTitle className="text-base">{p.name}</CardTitle></CardHeader>
                <CardContent className="space-y-3">
                  <div><Label className="text-xs">Price ($)</Label><Input type="number" step="0.01" defaultValue={p.price} className="mt-1 h-9 rounded-lg" id={`price-${p.id}`} /></div>
                  <div><Label className="text-xs">Credits</Label><Input type="number" defaultValue={p.credits} className="mt-1 h-9 rounded-lg" id={`credits-${p.id}`} /></div>
                  <Button size="sm" className="w-full rounded-full bg-blue-600 hover:bg-blue-700" onClick={() => {
                    const price = parseFloat(document.getElementById(`price-${p.id}`).value)
                    const credits = parseInt(document.getElementById(`credits-${p.id}`).value)
                    updatePlan(p.id, { price, credits })
                  }}>Save</Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="searches" className="mt-6">
          <DataCard empty={searches.length === 0} emptyText="No searches.">
            <Table>
              <TableHeader><TableRow><TableHead>Type</TableHead><TableHead>Query</TableHead><TableHead>Model</TableHead><TableHead>Unlocked</TableHead><TableHead>Date</TableHead></TableRow></TableHeader>
              <TableBody>
                {searches.map(s => (
                  <TableRow key={s.id}>
                    <TableCell><Badge variant="secondary" className="uppercase">{s.type}</Badge></TableCell>
                    <TableCell className="font-mono text-xs">{s.query}</TableCell>
                    <TableCell>{s.model}</TableCell>
                    <TableCell>{s.unlocked ? <CheckCircle2 className="h-4 w-4 text-green-600" /> : <XCircle className="h-4 w-4 text-slate-300" />}</TableCell>
                    <TableCell className="text-xs text-slate-500">{new Date(s.createdAt).toLocaleString()}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </DataCard>
        </TabsContent>

        <TabsContent value="orders" className="mt-6">
          <DataCard empty={orders.length === 0} emptyText="No orders.">
            <Table>
              <TableHeader><TableRow><TableHead>Plan</TableHead><TableHead>Credits</TableHead><TableHead>Amount</TableHead><TableHead>Status</TableHead><TableHead>Date</TableHead></TableRow></TableHeader>
              <TableBody>
                {orders.map(o => (
                  <TableRow key={o.id}>
                    <TableCell className="font-medium">{o.planName}</TableCell>
                    <TableCell>+{o.credits}</TableCell>
                    <TableCell>${o.amount}</TableCell>
                    <TableCell><Badge className="bg-green-600 hover:bg-green-600 capitalize">{o.status}</Badge></TableCell>
                    <TableCell className="text-xs text-slate-500">{new Date(o.createdAt).toLocaleString()}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </DataCard>
        </TabsContent>

        <TabsContent value="messages" className="mt-6">
          <DataCard empty={contacts.length === 0} emptyText="No messages.">
            <div className="space-y-3">
              {contacts.map(c => (
                <div key={c.id} className="rounded-xl border border-slate-100 p-4">
                  <div className="flex items-center justify-between"><p className="font-medium">{c.name} <span className="text-sm font-normal text-slate-500">· {c.email}</span></p><span className="text-xs text-slate-400">{new Date(c.createdAt).toLocaleString()}</span></div>
                  <p className="mt-1 text-sm text-slate-600">{c.message}</p>
                </div>
              ))}
            </div>
          </DataCard>
        </TabsContent>
      </Tabs>
    </div>
  )
}

// ==================================================================
// Footer
// ==================================================================
function Footer({ navigate, t }) {
  const cols = [
    ['Services', [['nav_imei', 'imei'], ['nav_serial', 'serial'], ['nav_pricing', 'pricing']]],
    ['Company', [['nav_contact', 'contact'], ['nav_faq', 'faq']]],
    ['Legal', [['Terms of Service', 'terms'], ['Privacy Policy', 'privacy']]],
  ]
  return (
    <footer className="border-t border-slate-100 bg-slate-50">
      <div className="container py-14">
        <div className="grid gap-10 md:grid-cols-4">
          <div>
            <div className="flex items-center gap-2">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 to-blue-400 text-white"><ScanLine className="h-5 w-5" /></div>
              <span className="text-lg font-bold">Unlock<span className="text-blue-600">Tap</span></span>
            </div>
            <p className="mt-3 max-w-xs text-sm text-slate-500">{t('footer_tag')}</p>
          </div>
          {cols.map(([title, links]) => (
            <div key={title}>
              <h4 className="text-sm font-semibold text-slate-900">{title}</h4>
              <ul className="mt-4 space-y-2">
                {links.map(([label, r]) => (
                  <li key={r}><button onClick={() => navigate(r)} className="text-sm text-slate-500 hover:text-blue-600">{T.en[label] ? t(label) : label}</button></li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <Separator className="my-8" />
        <div className="flex flex-col items-center justify-between gap-3 text-sm text-slate-400 sm:flex-row">
          <p>© {new Date().getFullYear()} UnlockTap. All rights reserved.</p>
          <p>Made for Apple device verification · Demo build</p>
        </div>
      </div>
    </footer>
  )
}
