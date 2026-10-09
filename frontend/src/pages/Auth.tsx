import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Sparkles } from 'lucide-react'
import { useAuth } from '../lib/store'
import { api } from '../lib/api'

export default function Auth({ mode }: { mode: 'login' | 'register' }) {
  const [f, setF] = useState({ name: '', email: '', password: '', confirm: '' })
  const [errs, setErrs] = useState<Record<string, string>>({})
  const [srv, setSrv] = useState(''); const [busy, setBusy] = useState(false)
  const { signIn } = useAuth(); const nav = useNavigate(); const reg = mode === 'register'
  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement>) => setF({ ...f, [k]: e.target.value })

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    const x: Record<string, string> = {}
    if (reg && f.name.trim().length < 2) x.name = 'Enter your full name'
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(f.email)) x.email = 'Enter a valid email address'
    if (f.password.length < 8) x.password = 'Password must be at least 8 characters'
    if (reg && f.confirm !== f.password) x.confirm = 'Passwords do not match'
    setErrs(x); if (Object.keys(x).length) return
    setSrv(''); setBusy(true)
    try {
      const r = reg ? await api.register(f.name.trim(), f.email.trim(), f.password) : await api.login(f.email.trim(), f.password)
      const p = await signIn(r.access_token, r.user)
      nav(p ? '/dashboard' : '/onboarding')
    } catch (err) { setSrv(err instanceof Error ? err.message : 'Something went wrong') }
    finally { setBusy(false) }
  }
  const fields: [string, string, string][] = [...(reg ? [['name', 'Full name', 'text']] as [string, string, string][] : []), ['email', 'Email', 'email'], ['password', 'Password', 'password'], ...(reg ? [['confirm', 'Confirm password', 'password']] as [string, string, string][] : [])]
  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <form onSubmit={submit} noValidate className="card w-full max-w-md space-y-4">
        <div className="flex items-center gap-2 font-bold"><Sparkles className="text-indigo-500" size={20} />AI CareerGuide</div>
        <h1 className="text-2xl font-bold">{reg ? 'Create your account' : 'Welcome back'}</h1>
        {fields.map(([k, label, type]) => (
          <div key={k}><label htmlFor={k} className="mb-1 block text-sm font-medium">{label}</label>
            <input id={k} type={type} className="input" value={f[k as keyof typeof f]} onChange={set(k)} autoComplete={k === 'password' ? (reg ? 'new-password' : 'current-password') : undefined} />
            {errs[k] && <p role="alert" className="mt-1 text-xs text-red-500">{errs[k]}</p>}</div>
        ))}
        {srv && <p role="alert" className="text-sm text-red-500">{srv}</p>}
        <button className="btn w-full" disabled={busy}>{busy ? 'Please wait…' : reg ? 'Sign up' : 'Log in'}</button>
        <p className="text-center text-sm">{reg ? <>Have an account? <Link className="text-indigo-500" to="/login">Log in</Link></> : <>New here? <Link className="text-indigo-500" to="/register">Create an account</Link></>}</p>
      </form>
    </div>
  )
}
