import { useEffect, useState } from 'react'
import { ExternalLink, Clock, Gift } from 'lucide-react'
import { api, type CareerInfo, type CourseRecs, type CourseStatus } from '../lib/api'

const tone: Record<string, string> = { beginner: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300', intermediate: 'bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300', advanced: 'bg-rose-100 text-rose-700 dark:bg-rose-950 dark:text-rose-300' }

export default function Courses() {
  const [careers, setCareers] = useState<CareerInfo[]>([]); const [sel, setSel] = useState('')
  const [st, setSt] = useState<Record<string, CourseStatus>>({}); const [d, setD] = useState<CourseRecs | null>(null); const [err, setErr] = useState('')
  useEffect(() => { api.careers().then(setCareers).catch(() => {}); api.courseStatuses().then(setSt).catch(() => {}) }, [])
  const track = (id: string, s: CourseStatus) => api.setCourseStatus(id, s).then(() => setSt(m => { const n = { ...m }; if (s === 'none') delete n[id]; else n[id] = s; return n })).catch(e => setErr(e.message))
  useEffect(() => { setErr(''); setD(null); api.courses(sel || undefined, 8).then(setD).catch(e => setErr(e.message)) }, [sel])
  return (
    <div className="mx-auto max-w-5xl space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div><h1 className="text-2xl font-bold">Recommended courses</h1>{d && <p className="text-sm text-slate-500">Targeting {d.career} ({d.match_score}% match)</p>}</div>
        <label className="text-sm">Target career<select className="input mt-1" value={sel} onChange={e => setSel(e.target.value)}><option value="">My goal / best match</option>{careers.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></label>
      </div>
      {err && <div role="alert" className="card text-sm text-red-600 dark:text-red-400">{err}</div>}
      {!d && !err && <div className="card text-sm text-slate-500">Finding courses…</div>}
      {d && !d.courses.length && <div className="card text-sm">No skill gaps found for this career, so there is nothing to recommend. Nice work.</div>}
      <div className="grid gap-4 md:grid-cols-2">
        {d?.courses.map((c, i) => (
          <div key={c.id} className="card flex flex-col">
            <div className="flex items-start justify-between gap-2"><h2 className="font-semibold"><span className="mr-2 text-indigo-500">{i + 1}.</span>{c.title}</h2>
              <span className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${tone[c.difficulty]}`}>{c.difficulty}</span></div>
            <p className="text-xs text-slate-500">{c.platform} · {c.provider}</p>
            <p className="mt-3 text-sm"><span className="font-medium">Why:</span> {c.reason}</p>
            <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-slate-500">
              <span className="flex items-center gap-1"><Clock size={12} />~{c.duration_hours}h</span>
              {c.free && <span className="flex items-center gap-1"><Gift size={12} />Free access</span>}
              {c.prerequisites.length > 0 && <span>Prereqs: {c.prerequisites.join(', ')}</span>}
            </div>
            <a href={c.url} target="_blank" rel="noopener noreferrer" className="btn mt-4 self-start">Open course <ExternalLink size={14} /></a>
            <label className="mt-3 text-xs text-slate-500">My progress <select className="input mt-1 !py-1 text-sm" value={st[c.id] ?? 'none'} onChange={e => track(c.id, e.target.value as CourseStatus)}><option value="none">Not started</option><option value="planned">Planned</option><option value="in_progress">In progress</option><option value="completed">Completed</option></select></label>
          </div>
        ))}
      </div>
      {d && d.uncovered_skills.length > 0 && <p className="text-sm text-slate-500">No course in our catalog yet for: {d.uncovered_skills.join(', ')}.</p>}
      <p className="text-xs text-slate-500">Durations are rough estimates and ratings are not shown because they are not verified. Check each provider for current pricing and content.</p>
    </div>
  )
}
