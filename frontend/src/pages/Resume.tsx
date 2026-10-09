import { useEffect, useRef, useState } from 'react'
import { Check, AlertTriangle, ExternalLink, UploadCloud } from 'lucide-react'
import { api, type CareerInfo, type ResumeResult } from '../lib/api'

const MAX_MB = 5
const label: Record<string, string> = { sections: 'Sections', quantified_impact: 'Quantified impact', skills_breadth: 'Skills breadth', length: 'Length', action_verbs: 'Action verbs' }
const Chips = ({ items, tone = 'indigo' }: { items: string[]; tone?: 'indigo' | 'amber' }) => items.length ? <div className="flex flex-wrap gap-2">{items.map(s => <span key={s} className={`rounded-full px-2 py-0.5 text-xs ${tone === 'amber' ? 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300' : 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300'}`}>{s}</span>)}</div> : <p className="text-sm text-slate-500">Nothing detected.</p>
const Bar = ({ name, v }: { name: string; v: number }) => (<div><div className="mb-1 flex justify-between text-sm"><span>{name}</span><span className="font-semibold">{v}%</span></div><div className="h-2 rounded-full bg-slate-200 dark:bg-slate-800"><div className="h-2 rounded-full bg-indigo-500" style={{ width: `${v}%` }} /></div></div>)

export default function Resume() {
  const [careers, setCareers] = useState<CareerInfo[]>([]); const [sel, setSel] = useState('')
  const [r, setR] = useState<ResumeResult | null>(null); const [err, setErr] = useState(''); const [busy, setBusy] = useState(false)
  const input = useRef<HTMLInputElement>(null)
  useEffect(() => { api.careers().then(setCareers).catch(() => {}); api.latestResume().then(x => x && setR(x)).catch(() => {}) }, [])

  async function submit(e: React.FormEvent) {
    e.preventDefault(); setErr('')
    const f = input.current?.files?.[0]
    if (!f) return setErr('Choose a PDF file first')
    if (!f.name.toLowerCase().endsWith('.pdf')) return setErr('Only PDF files are supported')
    if (f.size > MAX_MB * 1024 * 1024) return setErr(`File is larger than ${MAX_MB} MB`)
    setBusy(true)
    try { setR(await api.analyzeResume(f, sel || undefined)) } catch (x) { setErr(x instanceof Error ? x.message : 'Upload failed') } finally { setBusy(false) }
  }
  return (
    <div className="mx-auto max-w-4xl space-y-5">
      <h1 className="text-2xl font-bold">Resume analyzer</h1>
      <form onSubmit={submit} className="card flex flex-wrap items-end gap-3">
        <label className="min-w-56 flex-1 text-sm font-medium">Resume (PDF, up to {MAX_MB} MB)<input ref={input} type="file" accept="application/pdf,.pdf" className="input mt-1 font-normal" /></label>
        <label className="text-sm font-medium">Target role<select className="input mt-1 font-normal" value={sel} onChange={e => setSel(e.target.value)}><option value="">My goal / best match</option>{careers.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></label>
        <button className="btn" disabled={busy}><UploadCloud size={16} />{busy ? 'Analyzing…' : 'Analyze resume'}</button>
        <p className="w-full text-xs text-slate-500">Only the analysis is saved. Your PDF and its raw text are not stored.</p>
      </form>
      {err && <div role="alert" className="card text-sm text-red-600 dark:text-red-400">{err}</div>}
      {r && <>
        <div className="grid gap-4 md:grid-cols-3">
          <div className="card text-center"><div className="text-sm text-slate-500">Resume score</div><div className="text-5xl font-extrabold text-indigo-600 dark:text-indigo-400">{r.resume_score}<span className="text-xl text-slate-400">/100</span></div>
            <div className="mt-3 space-y-1 text-left text-xs text-slate-500">{Object.entries(r.score_breakdown).map(([k, v]) => <div key={k} className="flex justify-between"><span>{label[k] ?? k}</span><span>{v.points}/{v.max}</span></div>)}</div></div>
          <div className="card md:col-span-2 space-y-3"><h2 className="font-semibold">Resume vs {r.target.career}</h2>
            <Bar name="Skill match" v={r.role_match.skills} /><Bar name="Project match" v={r.role_match.projects} /><Bar name="Experience match" v={r.role_match.experience} />
            <div className="border-t border-slate-200 pt-2 text-sm font-semibold dark:border-slate-800">Overall: {r.role_match.overall}%</div></div>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="card"><h2 className="mb-2 font-semibold">Strengths</h2>{r.strengths.length ? <ul className="space-y-1 text-sm">{r.strengths.map(s => <li key={s} className="flex gap-2"><Check size={14} className="mt-1 shrink-0 text-emerald-500" />{s}</li>)}</ul> : <p className="text-sm text-slate-500">No standout strengths detected yet.</p>}</div>
          <div className="card"><h2 className="mb-2 font-semibold">Missing keywords</h2><Chips items={r.missing_keywords} tone="amber" /></div>
          <div className="card"><h2 className="mb-2 font-semibold">ATS suggestions</h2><ul className="space-y-2 text-sm">{r.ats_suggestions.map(s => <li key={s} className="flex gap-2"><AlertTriangle size={14} className="mt-1 shrink-0 text-amber-500" />{s}</li>)}</ul></div>
          <div className="card"><h2 className="mb-2 font-semibold">Project suggestions</h2><ul className="list-disc space-y-2 pl-5 text-sm">{r.project_suggestions.length ? r.project_suggestions.map(s => <li key={s}>{s}</li>) : <li>Your projects already cover the core skills for this role.</li>}</ul></div>
        </div>
        {r.recommended_courses.length > 0 && <div className="card"><h2 className="mb-2 font-semibold">Courses for your technical gaps</h2><ul className="space-y-2 text-sm">{r.recommended_courses.map(c => <li key={c.id}><a className="inline-flex items-center gap-1 font-medium text-indigo-600 hover:underline dark:text-indigo-400" href={c.url} target="_blank" rel="noopener noreferrer">{c.title}<ExternalLink size={12} /></a><div className="text-xs text-slate-500">{c.reason}</div></li>)}</ul></div>}
        <details className="card"><summary className="cursor-pointer font-semibold">What we extracted (please check it)</summary>
          <div className="mt-3 space-y-3 text-sm"><p><span className="font-medium">Name:</span> {r.name ?? 'not detected'}</p>
            {([['Education', r.extracted.education], ['Skills', r.extracted.skills], ['Technologies used in projects/experience', r.extracted.technologies], ['Projects', r.extracted.projects], ['Experience', r.extracted.experience], ['Certifications', r.extracted.certifications]] as [string, string[]][]).map(([t, v]) => <div key={t}><div className="mb-1 font-medium">{t}</div>{t === 'Skills' || t.startsWith('Tech') ? <Chips items={v} /> : v.length ? <ul className="list-disc pl-5 text-slate-600 dark:text-slate-400">{v.map(x => <li key={x}>{x}</li>)}</ul> : <p className="text-slate-500">Nothing detected.</p>}</div>)}</div></details>
        <p className="text-xs text-slate-500">{r.disclaimer}</p>
      </>}
    </div>
  )
}
