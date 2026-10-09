import { useEffect, useState } from 'react'
import { Check, AlertTriangle, ExternalLink, Search } from 'lucide-react'
import { api, type JobHistoryItem, type JobResult } from '../lib/api'

const MAX = 20000
const Chips = ({ items }: { items: string[] }) => items.length ? <div className="flex flex-wrap gap-2">{items.map(s => <span key={s} className="rounded-full bg-indigo-50 px-2 py-0.5 text-xs text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300">{s}</span>)}</div> : <p className="text-sm text-slate-500">None found.</p>

export default function JobMatch() {
  const [text, setText] = useState(''); const [title, setTitle] = useState('')
  const [r, setR] = useState<JobResult | null>(null); const [hist, setHist] = useState<JobHistoryItem[]>([])
  const [err, setErr] = useState(''); const [busy, setBusy] = useState(false)
  const refresh = () => api.jobHistory().then(setHist).catch(() => {})
  useEffect(() => { refresh() }, [])

  async function submit(e: React.FormEvent) {
    e.preventDefault(); setErr('')
    if (text.trim().length < 50) return setErr('Paste the full job description (at least 50 characters)')
    setBusy(true)
    try { setR(await api.analyzeJob(text, title)); refresh() } catch (x) { setErr(x instanceof Error ? x.message : 'Analysis failed') } finally { setBusy(false) }
  }
  const open = (id: string) => api.jobById(id).then(setR).catch(x => setErr(x.message))

  return (
    <div className="mx-auto max-w-4xl space-y-5">
      <h1 className="text-2xl font-bold">Job description match</h1>
      <form onSubmit={submit} className="card space-y-3">
        <label className="block text-sm font-medium">Job title <span className="font-normal text-slate-500">(optional)</span><input className="input mt-1 font-normal" maxLength={120} value={title} onChange={e => setTitle(e.target.value)} /></label>
        <label className="block text-sm font-medium">Job description<textarea rows={9} maxLength={MAX} className="input mt-1 font-normal" placeholder="Paste the job posting here…" value={text} onChange={e => setText(e.target.value)} /></label>
        <div className="flex items-center justify-between"><span className="text-xs text-slate-500">{text.length}/{MAX} · compared against your saved skills · the pasted text is not stored</span>
          <button className="btn" disabled={busy}><Search size={16} />{busy ? 'Analyzing…' : 'Analyze job match'}</button></div>
      </form>
      {err && <div role="alert" className="card text-sm text-red-600 dark:text-red-400">{err}</div>}
      {hist.length > 0 && <div className="card"><h2 className="mb-2 text-sm font-semibold">Recent analyses</h2><ul className="flex flex-wrap gap-2">{hist.map(h => <li key={h.id}><button className="btn-ghost !py-1 text-xs" onClick={() => open(h.id)}>{h.title} · {h.match_score}%</button></li>)}</ul></div>}
      {r && <>
        <div className="card bg-gradient-to-br from-indigo-600 to-violet-600 !text-white"><div className="text-sm opacity-80">Job match{r.title ? ` · ${r.title}` : ''}</div><div className="text-5xl font-extrabold">{r.match_score}%</div>
          <div className="mt-1 text-sm opacity-90">Required skills: {r.breakdown.required_match ?? 'n/a'}% · Preferred skills: {r.breakdown.preferred_match ?? 'n/a'}%</div></div>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="card"><h2 className="mb-2 font-semibold">You already have</h2>{r.you_have.length ? <ul className="space-y-1 text-sm">{r.you_have.map(s => <li key={s} className="flex items-center gap-2"><Check size={14} className="text-emerald-500" />{s}</li>)}</ul> : <p className="text-sm text-slate-500">No matching skills in your profile yet.</p>}</div>
          <div className="card"><h2 className="mb-2 font-semibold">You should improve</h2><ul className="space-y-1 text-sm">{r.should_improve.map(s => <li key={s} className="flex items-center gap-2"><AlertTriangle size={14} className="text-amber-500" />{s} <span className="text-xs text-slate-500">(required)</span></li>)}
            {r.preferred_missing.map(s => <li key={s} className="flex items-center gap-2"><AlertTriangle size={14} className="text-slate-400" />{s} <span className="text-xs text-slate-500">(preferred)</span></li>)}
            {!r.should_improve.length && !r.preferred_missing.length && <li className="text-slate-500">Nothing missing. Strong match.</li>}</ul></div>
          <div className="card"><h2 className="mb-2 font-semibold">Required skills</h2><Chips items={r.required_skills} /><h2 className="mb-2 mt-4 font-semibold">Preferred skills</h2><Chips items={r.preferred_skills} /></div>
          <div className="card space-y-3 text-sm"><div><h2 className="mb-1 font-semibold">Experience</h2>{r.experience_requirements.length ? <ul className="list-disc space-y-1 pl-5">{r.experience_requirements.map(x => <li key={x.context}>{x.min_years}+ years: <span className="text-slate-500">{x.context}</span></li>)}</ul> : <p className="text-slate-500">No years of experience mentioned.</p>}</div>
            <div><h2 className="mb-1 font-semibold">Education</h2>{r.education_requirements.mentions.length ? <ul className="list-disc space-y-1 pl-5">{r.education_requirements.mentions.map(x => <li key={x}>{x}</li>)}</ul> : <p className="text-slate-500">No education requirement mentioned.</p>}</div>
            <div><h2 className="mb-1 font-semibold">Technologies mentioned</h2><Chips items={r.technologies} /></div></div>
        </div>
        {r.recommended_courses.length > 0 && <div className="card"><h2 className="mb-2 font-semibold">Courses for the missing skills</h2><ul className="space-y-2 text-sm">{r.recommended_courses.map(c => <li key={c.id}><a className="inline-flex items-center gap-1 font-medium text-indigo-600 hover:underline dark:text-indigo-400" href={c.url} target="_blank" rel="noopener noreferrer">{c.title}<ExternalLink size={12} /></a><div className="text-xs text-slate-500">{c.reason}</div></li>)}</ul></div>}
        <p className="text-xs text-slate-500">{r.disclaimer}</p>
      </>}
    </div>
  )
}
