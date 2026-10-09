import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { ExternalLink, PlusCircle } from 'lucide-react'
import { api, type CourseStatus, type ProgressSummary } from '../lib/api'

const names: Record<string, string> = { skills: 'Skills', roadmap: 'Roadmap', portfolio: 'Portfolio', courses: 'Courses' }
const opts: [CourseStatus, string][] = [['planned', 'Planned'], ['in_progress', 'In progress'], ['completed', 'Completed'], ['none', 'Remove']]
const Stat = ({ label, value }: { label: string; value: string | number }) => <div className="card text-center"><div className="text-2xl font-extrabold">{value}</div><div className="text-xs text-slate-500">{label}</div></div>

export default function Progress() {
  const [p, setP] = useState<ProgressSummary | null>(null); const [err, setErr] = useState(''); const [busy, setBusy] = useState(false); const nav = useNavigate()
  useEffect(() => { api.progress().then(setP).catch(e => setErr(e.message)) }, [])
  const run = async (fn: () => Promise<ProgressSummary>) => { setBusy(true); setErr(''); try { setP(await fn()) } catch (e) { setErr(e instanceof Error ? e.message : 'Failed') } finally { setBusy(false) } }

  if (!p) return <div className="mx-auto max-w-3xl">{err ? <div role="alert" className="card text-sm text-red-600 dark:text-red-400">{err}</div> : <div className="card text-sm text-slate-500">Loading your progress…</div>}</div>
  const hist = p.history.map(h => ({ ...h, label: new Date(h.at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) }))
  const parts = Object.entries(p.readiness_breakdown).map(([k, v]) => ({ name: names[k] ?? k, value: v.value }))
  const first = p.history[0], gained = p.skills.total_skills - (first?.skill_count ?? p.skills.total_skills)
  return (
    <div className="mx-auto max-w-5xl space-y-5">
      <h1 className="text-2xl font-bold">Progress tracking</h1>
      {err && <div role="alert" className="card text-sm text-red-600 dark:text-red-400">{err}</div>}
      <div className="grid gap-4 md:grid-cols-3">
        <div className="card bg-gradient-to-br from-indigo-600 to-violet-600 !text-white md:col-span-1"><div className="text-sm opacity-80">Career readiness · {p.career}</div><div className="text-6xl font-extrabold">{p.readiness_score}%</div>
          <div className="mt-2 space-y-0.5 text-xs opacity-90">{Object.entries(p.readiness_breakdown).map(([k, v]) => <div key={k} className="flex justify-between"><span>{names[k]} ({v.weight}%)</span><span>{v.points} pts</span></div>)}</div></div>
        <div className="grid grid-cols-2 gap-4 md:col-span-2"><Stat label="Core skill coverage" value={`${p.skills.coverage_percent}%`} /><Stat label="Roadmap complete" value={p.roadmap.exists ? `${p.roadmap.completed}/${p.roadmap.total} phases` : 'Not started'} />
          <Stat label="Courses completed" value={`${p.courses.completed}/${p.courses.tracked}`} /><Stat label="Skills since first check" value={`${gained >= 0 ? '+' : ''}${gained}`} /></div>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card"><h2 className="mb-3 font-semibold">Readiness over time</h2>
          {hist.length < 2 ? <p className="text-sm text-slate-500">Your history builds up as you complete courses, roadmap phases and add skills. Currently {p.readiness_score}%.</p> :
            <div className="h-56"><ResponsiveContainer><LineChart data={hist}><CartesianGrid strokeDasharray="3 3" opacity={0.3} /><XAxis dataKey="label" /><YAxis domain={[0, 100]} /><Tooltip /><Legend />
              <Line type="monotone" dataKey="readiness" name="Readiness %" stroke="#6366f1" strokeWidth={2} /><Line type="monotone" dataKey="roadmap_percent" name="Roadmap %" stroke="#10b981" strokeWidth={2} /></LineChart></ResponsiveContainer></div>}</div>
        <div className="card"><h2 className="mb-3 font-semibold">What makes up your score</h2>
          <div className="h-56"><ResponsiveContainer><BarChart data={parts}><CartesianGrid strokeDasharray="3 3" opacity={0.3} /><XAxis dataKey="name" /><YAxis domain={[0, 100]} /><Tooltip /><Bar dataKey="value" name="Value %" fill="#8b5cf6" radius={[6, 6, 0, 0]} /></BarChart></ResponsiveContainer></div></div>
      </div>
      {p.pending_skills.length > 0 && <div className="card border-emerald-300"><h2 className="font-semibold">New skills you may have acquired</h2>
        <p className="mt-1 text-sm text-slate-500">From completed courses and roadmap phases. Add the ones you are confident in to your profile so your matches and gaps update.</p>
        <div className="mt-3 flex flex-wrap gap-2">{p.pending_skills.map(s => <button key={s} disabled={busy} onClick={() => run(() => api.applySkills([s]))} className="btn-ghost !py-1 text-xs"><PlusCircle size={12} />{s}</button>)}</div>
        <button className="btn mt-3" disabled={busy} onClick={() => run(() => api.applySkills())}>Add all to my profile</button>
        <p className="mt-2 text-xs text-slate-500">Your saved roadmap does not change automatically. Use Regenerate on the Roadmap page afterwards.</p></div>}
      <div className="card"><h2 className="mb-3 font-semibold">Courses</h2>
        {!p.courses.items.length ? <p className="text-sm text-slate-500">No courses tracked yet. Mark courses as planned, in progress or completed on the Courses page.</p> :
          <ul className="divide-y divide-slate-200 dark:divide-slate-800">{p.courses.items.map(c => (
            <li key={c.course_id} className="flex flex-wrap items-center justify-between gap-2 py-2 text-sm">
              <a className="inline-flex items-center gap-1 font-medium text-indigo-600 hover:underline dark:text-indigo-400" href={c.url} target="_blank" rel="noopener noreferrer">{c.title}<ExternalLink size={12} /></a>
              <select aria-label={`Status of ${c.title}`} className="input !w-auto !py-1" value={c.status} disabled={busy} onChange={e => run(() => api.setCourseStatus(c.course_id, e.target.value as CourseStatus))}>{opts.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select>
            </li>))}</ul>}</div>
      <div className="grid gap-4 md:grid-cols-2">
        <div className="card"><h2 className="mb-2 font-semibold">Projects ({p.portfolio.projects.length})</h2>{p.portfolio.projects.length ? <ul className="list-disc space-y-1 pl-5 text-sm">{p.portfolio.projects.map(x => <li key={x}>{x}</li>)}</ul> : <p className="text-sm text-slate-500">None listed yet.</p>}</div>
        <div className="card"><h2 className="mb-2 font-semibold">Certifications ({p.portfolio.certifications.length})</h2>{p.portfolio.certifications.length ? <ul className="list-disc space-y-1 pl-5 text-sm">{p.portfolio.certifications.map(x => <li key={x}>{x}</li>)}</ul> : <p className="text-sm text-slate-500">None listed yet.</p>}</div>
      </div>
      <div className="flex flex-wrap items-center gap-3"><button className="btn-ghost" onClick={() => nav('/onboarding')}>Edit projects and certifications</button><p className="text-xs text-slate-500">{p.disclaimer}</p></div>
    </div>
  )
}
