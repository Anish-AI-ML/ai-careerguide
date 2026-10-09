import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Check, AlertTriangle, FileText, Map, BookOpen, Bot, Briefcase, Compass } from 'lucide-react'
import { analyze, api, type Analysis, type Course } from '../lib/api'
import { useAuth } from '../lib/store'

const actions = [[FileText, 'Analyze Resume', '/resume'], [Compass, 'Explore Careers', '/dashboard'], [BookOpen, 'Find Courses', '/courses'], [Bot, 'CareerAI', '/careerai'], [Briefcase, 'Job Match', '/job-match'], [Map, 'View Roadmap', '/roadmap']] as const

export default function Dashboard() {
  const { user, profile } = useAuth(); const [d, setD] = useState<Analysis | null>(null); const [err, setErr] = useState(''); const [tick, setTick] = useState(0); const [cs, setCs] = useState<Course[]>([]); const [rmp, setRmp] = useState<number | null>(null); const [ready, setReady] = useState<number | null>(null)
  useEffect(() => { setErr(''); if (profile) analyze(profile).then(setD).catch(e => setErr(e.message)) }, [tick, profile])
  useEffect(() => { api.progress().then(r => setReady(r.readiness_score)).catch(() => {}) }, [profile])
  useEffect(() => { api.roadmap().then(r => setRmp(r.progress_percent)).catch(() => {}) }, [profile])
  useEffect(() => { api.courses(undefined, 3).then(r => setCs(r.courses)).catch(() => {}) }, [profile])
  const t = d?.top
  const cov = t ? Math.round(100 * t.strengths.length / Math.max(1, t.strengths.length + t.skill_gaps.length)) : 0
  const chart = d ? [d.top, ...d.alternatives].map(m => ({ name: m.career, score: m.match_score })) : []
  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <h1 className="text-2xl font-bold">Welcome back, {user?.name} 👋</h1>
      {err && <div role="alert" className="card border-red-300 text-sm text-red-600 dark:text-red-400">{err}<button className="btn-ghost ml-3" onClick={() => setTick(tick + 1)}>Retry</button></div>}
      {!d && !err && <div className="card text-sm text-slate-500">Analyzing your profile…</div>}
      {t && d && <>
        <div className="grid gap-4 md:grid-cols-3">
          <div className="card md:col-span-2 bg-gradient-to-br from-indigo-600 to-violet-600 !text-white">
            <div className="text-sm opacity-80">Top career match</div><div className="mt-1 text-3xl font-extrabold">{t.career}</div><div className="text-5xl font-extrabold">{t.match_score}% <span className="text-lg font-medium opacity-80">match</span></div>
            <p className="mt-2 text-sm opacity-90">{t.reason}</p>
          </div>
          <div className="card"><div className="text-sm text-slate-500">Core skill coverage</div><div className="mt-1 text-4xl font-extrabold">{cov}%</div><div className="mt-3 h-2 rounded-full bg-slate-200 dark:bg-slate-800"><div className="h-2 rounded-full bg-indigo-500" style={{ width: `${cov}%` }} /></div>
            <div className="mt-4 text-sm text-slate-500">Career readiness</div><div className="text-2xl font-bold">{ready === null ? '…' : `${ready}%`}</div><div className="mt-3 text-sm text-slate-500">Roadmap progress</div><div className="text-2xl font-bold">{rmp === null ? '…' : `${rmp}%`}</div></div>
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="card"><h2 className="mb-3 font-semibold">Career recommendations</h2>
            <div className="h-64"><ResponsiveContainer><BarChart data={chart} layout="vertical" margin={{ left: 10 }}><CartesianGrid strokeDasharray="3 3" opacity={0.3} /><XAxis type="number" domain={[0, 100]} /><YAxis type="category" dataKey="name" width={140} tick={{ fontSize: 12 }} /><Tooltip /><Bar dataKey="score" fill="#6366f1" radius={[0, 6, 6, 0]} /></BarChart></ResponsiveContainer></div></div>
          <div className="card"><h2 className="mb-3 font-semibold">Why {t.career}?</h2>
            <ul className="space-y-1 text-sm">{t.strengths.map(s => <li key={s} className="flex items-center gap-2"><Check size={14} className="text-emerald-500" />{s}</li>)}
              {t.skill_gaps.map(s => <li key={s} className="flex items-center gap-2"><AlertTriangle size={14} className="text-amber-500" />Improve: {s}</li>)}</ul>
            <p className="mt-3 text-xs text-slate-500">{t.disclaimer}</p></div>
        </div>
      </>}
      {cs.length > 0 && <div className="card"><div className="mb-3 flex items-center justify-between"><h2 className="font-semibold">Recommended courses</h2><Link to="/courses" className="text-sm text-indigo-500">See all</Link></div>
        <ul className="space-y-2 text-sm">{cs.map(c => <li key={c.id}><a className="font-medium text-indigo-600 hover:underline dark:text-indigo-400" href={c.url} target="_blank" rel="noopener noreferrer">{c.title}</a><div className="text-xs text-slate-500">{c.reason}</div></li>)}</ul></div>}
      <div><h2 className="mb-3 font-semibold">Quick actions</h2><div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
        {actions.map(([I, l, to]) => <Link key={l} to={to} className="card flex flex-col items-center gap-2 text-center text-sm font-medium transition hover:border-indigo-400"><I className="text-indigo-500" />{l}</Link>)}</div></div>
    </div>
  )
}
