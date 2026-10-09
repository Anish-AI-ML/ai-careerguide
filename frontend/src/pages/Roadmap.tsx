import { useEffect, useState } from 'react'
import { CheckCircle2, Circle, Clock, FlaskConical, RefreshCw, Trophy, ExternalLink } from 'lucide-react'
import { api, type CareerInfo, type Roadmap as RM } from '../lib/api'

export default function Roadmap() {
  const [rm, setRm] = useState<RM | null>(null); const [err, setErr] = useState(''); const [busy, setBusy] = useState(false)
  const [careers, setCareers] = useState<CareerInfo[]>([]); const [sel, setSel] = useState('')
  useEffect(() => { api.careers().then(setCareers).catch(() => {}); api.roadmap().then(r => { setRm(r); setSel(r.career_id) }).catch(e => setErr(e.message)) }, [])

  async function regenerate() {
    setBusy(true); setErr('')
    try { const r = await api.generateRoadmap(sel || undefined); setRm(r); setSel(r.career_id) } catch (e) { setErr(e instanceof Error ? e.message : 'Failed') } finally { setBusy(false) }
  }
  async function toggle(id: string, completed: boolean) {
    if (!rm) return
    const prev = rm
    setRm({ ...rm, items: rm.items.map(i => (i.id === id ? { ...i, completed } : i)) })  // optimistic
    try { setRm(await api.setRoadmapItem(id, completed)) } catch (e) { setRm(prev); setErr(e instanceof Error ? e.message : 'Could not update') }
  }
  return (
    <div className="mx-auto max-w-3xl space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div><h1 className="text-2xl font-bold">Learning roadmap</h1>{rm && <p className="text-sm text-slate-500">Path to {rm.career} · about {rm.total_weeks} weeks at ~8 hours/week</p>}</div>
        <div className="flex items-end gap-2">
          <label className="text-sm">Target<select className="input mt-1" value={sel} onChange={e => setSel(e.target.value)}>{careers.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></label>
          <button className="btn-ghost" disabled={busy} onClick={regenerate}><RefreshCw size={14} className={busy ? 'animate-spin' : ''} />Regenerate</button>
        </div>
      </div>
      {err && <div role="alert" className="card text-sm text-red-600 dark:text-red-400">{err}</div>}
      {!rm && !err && <div className="card text-sm text-slate-500">Building your roadmap…</div>}
      {rm && <>
        <div className="card"><div className="mb-2 flex justify-between text-sm"><span>Progress</span><span className="font-semibold">{rm.progress_percent}%</span></div>
          <div className="h-2 rounded-full bg-slate-200 dark:bg-slate-800"><div className="h-2 rounded-full bg-gradient-to-r from-indigo-500 to-violet-500 transition-all" style={{ width: `${rm.progress_percent}%` }} /></div></div>
        {!rm.items.length && <div className="card text-sm">You already cover this career's core skills, so there are no phases to complete. Try a different target.</div>}
        <ol className="space-y-4">
          {rm.items.map(i => (
            <li key={i.id} className={`card ${i.completed ? 'opacity-70' : ''}`}>
              <div className="flex items-start justify-between gap-3">
                <div><div className="text-xs font-semibold uppercase tracking-wide text-indigo-500">Phase {i.phase}</div><h2 className="text-lg font-semibold">{i.title}</h2></div>
                <button onClick={() => toggle(i.id, !i.completed)} aria-pressed={i.completed} className="btn-ghost shrink-0">{i.completed ? <CheckCircle2 size={16} className="text-emerald-500" /> : <Circle size={16} />}{i.completed ? 'Completed' : 'Mark complete'}</button>
              </div>
              <div className="mt-2 flex flex-wrap gap-2 text-xs">{i.skills.map(s => <span key={s} className="rounded-full bg-indigo-50 px-2 py-0.5 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300">{s}</span>)}
                <span className="flex items-center gap-1 text-slate-500"><Clock size={12} />~{i.est_weeks} wk · {i.difficulty}</span></div>
              {i.courses.length > 0 && <div className="mt-3 text-sm"><div className="mb-1 font-medium">Courses</div><ul className="space-y-1">{i.courses.map(c => <li key={c.id}><a href={c.url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-indigo-600 hover:underline dark:text-indigo-400">{c.title}<ExternalLink size={12} /></a> <span className="text-xs text-slate-500">· {c.platform}</span></li>)}</ul></div>}
              <div className="mt-3 text-sm"><div className="mb-1 flex items-center gap-1 font-medium"><FlaskConical size={14} />Project ideas</div><ul className="list-disc space-y-1 pl-5 text-slate-600 dark:text-slate-400">{i.projects.map(p => <li key={p}>{p}</li>)}</ul></div>
            </li>
          ))}
        </ol>
        <div className="card flex items-center gap-3 border-indigo-300 bg-indigo-50 dark:bg-indigo-950"><Trophy className="text-indigo-500" /><div><div className="text-xs text-slate-500">Destination</div><div className="font-semibold">{rm.career}</div></div></div>
        <p className="text-xs text-slate-500">Estimates assume ~8 study hours a week and are rough guides, not guarantees.</p>
      </>}
    </div>
  )
}
