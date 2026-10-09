import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { emptyProfile, useAuth, type Profile } from '../lib/store'
import { api } from '../lib/api'

const SKILLS = ['Python', 'C++', 'Java', 'JavaScript', 'TypeScript', 'React', 'SQL', 'MongoDB', 'Machine Learning', 'Deep Learning', 'NLP', 'Computer Vision', 'TensorFlow', 'PyTorch', 'Cloud', 'Docker', 'Git', 'Statistics', 'Pandas', 'Linux']
const INTERESTS = ['Artificial Intelligence', 'Machine Learning', 'Data Science', 'Web Development', 'Cybersecurity', 'Cloud Computing', 'DevOps', 'Mobile Development', 'Robotics', 'Computer Vision', 'NLP', 'Data Analytics']
const GOALS = ['AI/ML Engineer', 'Data Scientist', 'Data Analyst', 'Software Engineer', 'Full Stack Developer', 'Data Engineer', 'Cloud Engineer', 'DevOps Engineer', 'Cybersecurity Engineer', 'Computer Vision Engineer', 'NLP Engineer', 'Other', "I'm not sure yet"]
const STEPS = ['Education', 'Technical skills', 'Interests', 'Experience', 'Career goal']

function Chips({ options, value, onChange, allowCustom }: { options: string[]; value: string[]; onChange: (v: string[]) => void; allowCustom?: boolean }) {
  const [txt, setTxt] = useState('')
  const all = [...options, ...value.filter(v => !options.includes(v))]
  const toggle = (o: string) => onChange(value.includes(o) ? value.filter(v => v !== o) : [...value, o])
  const add = () => { const t = txt.trim().slice(0, 60); if (t && !value.includes(t)) onChange([...value, t]); setTxt('') }
  return (<div>
    <div className="flex flex-wrap gap-2">{all.map(o => <button type="button" key={o} aria-pressed={value.includes(o)} onClick={() => toggle(o)} className={`rounded-full border px-3 py-1.5 text-sm ${value.includes(o) ? 'border-indigo-500 bg-indigo-50 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300' : 'border-slate-300 dark:border-slate-700'}`}>{o}</button>)}</div>
    {allowCustom && <div className="mt-3 flex gap-2"><input className="input" placeholder="Add a custom skill" value={txt} onChange={e => setTxt(e.target.value)} onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), add())} /><button type="button" className="btn-ghost" onClick={add}>Add</button></div>}
  </div>)
}

export default function Onboarding() {
  const { profile, setProfile } = useAuth()
  const [p, setP] = useState<Profile>(profile ?? emptyProfile); const [busy, setBusy] = useState(false)
  const [step, setStep] = useState(0); const [err, setErr] = useState(''); const nav = useNavigate()
  const up = (k: keyof Profile) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => setP({ ...p, [k]: e.target.value })

  function validate(): string {
    if (step === 0) { const c = Number(p.cgpa); if (!p.degree.trim() || !p.branch.trim()) return 'Degree and branch are required'; if (p.cgpa === '' || isNaN(c) || c < 0 || c > 10) return 'CGPA must be a number between 0 and 10' }
    if (step === 1 && !p.skills.length) return 'Select or add at least one skill'
    if (step === 2 && !p.interests.length) return 'Select at least one interest'
    if (step === 4 && !p.goal) return 'Choose a career goal or "I\'m not sure yet"'
    return ''
  }
  const next = async () => {
    const e = validate(); setErr(e); if (e) return
    if (step < 4) return setStep(step + 1)
    setBusy(true)
    try { setProfile(await api.saveProfile(p)); nav('/dashboard') }
    catch (x) { setErr(x instanceof Error ? x.message : 'Could not save your profile') }
    finally { setBusy(false) }
  }
  const Field = ({ k, label, type = 'text' }: { k: keyof Profile; label: string; type?: string }) => (<div><label className="mb-1 block text-sm font-medium">{label}<input type={type} className="input mt-1 font-normal" value={p[k] as string} onChange={up(k)} /></label></div>)
  const Area = ({ k, label }: { k: keyof Profile; label: string }) => (<label className="block text-sm font-medium">{label} <span className="font-normal text-slate-500">(one per line)</span><textarea rows={3} className="input mt-1 font-normal" value={p[k] as string} onChange={up(k)} /></label>)

  return (
    <div className="mx-auto max-w-2xl p-4 md:py-12">
      <div className="mb-6 flex gap-1" aria-label={`Step ${step + 1} of 5`}>{STEPS.map((s, i) => <div key={s} className={`h-1.5 flex-1 rounded-full ${i <= step ? 'bg-indigo-500' : 'bg-slate-200 dark:bg-slate-800'}`} />)}</div>
      <div className="card space-y-4">
        <h1 className="text-xl font-bold">Step {step + 1}: {STEPS[step]}</h1>
        {step === 0 && <div className="grid gap-3 sm:grid-cols-2"><Field k="degree" label="Degree (e.g. B.E.)" /><Field k="branch" label="Branch / specialization" /><Field k="institution" label="University / college" /><Field k="year" label="Current year" type="number" /><Field k="cgpa" label="CGPA (out of 10)" type="number" /></div>}
        {step === 1 && <Chips options={SKILLS} value={p.skills} onChange={skills => setP({ ...p, skills })} allowCustom />}
        {step === 2 && <Chips options={INTERESTS} value={p.interests} onChange={interests => setP({ ...p, interests })} />}
        {step === 3 && <div className="space-y-3"><Area k="projects" label="Projects" /><Area k="certifications" label="Certifications" /><Area k="experience" label="Internships, hackathons, open-source" /></div>}
        {step === 4 && <div><p className="mb-3 text-sm">What career are you interested in?</p><div className="flex flex-wrap gap-2">{GOALS.map(g => <button type="button" key={g} aria-pressed={p.goal === g} onClick={() => setP({ ...p, goal: g })} className={`rounded-full border px-3 py-1.5 text-sm ${p.goal === g ? 'border-indigo-500 bg-indigo-50 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300' : 'border-slate-300 dark:border-slate-700'}`}>{g}</button>)}</div>
          {p.goal === "I'm not sure yet" && <p className="mt-3 text-sm text-slate-500">We'll rank all careers using your full profile.</p>}</div>}
        {err && <p role="alert" className="text-sm text-red-500">{err}</p>}
        <div className="flex justify-between"><button className="btn-ghost" disabled={!step} onClick={() => { setErr(''); setStep(step - 1) }}>Back</button><button className="btn" disabled={busy} onClick={next}>{step === 4 ? (busy ? 'Saving…' : 'Analyze my profile') : 'Next'}</button></div>
      </div>
    </div>
  )
}
