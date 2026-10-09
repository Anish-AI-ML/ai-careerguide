import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Target, BarChart3, Map, BookOpen, FileText, Bot, Sparkles, Moon, Sun } from 'lucide-react'
import { useTheme } from '../layouts/AppShell'

const features = [
  [Target, 'Career match scores', 'Transparent, weighted scoring across skills, interests, education, projects and experience.'],
  [BarChart3, 'Skill-gap analysis', 'See exactly which required skills you have and which are missing.'],
  [Map, 'Learning roadmap', 'A phased plan built from your gaps (coming in the next phase).'],
  [BookOpen, 'Course recommendations', 'Courses matched to your gaps and target role (coming soon).'],
  [FileText, 'Resume & job analysis', 'Score your resume and compare it to job descriptions (coming soon).'],
  [Bot, 'CareerAI assistant', 'Ask questions grounded in your own profile (coming soon).'],
] as const
const faqs = [
  ['How are match scores calculated?', 'Each career is scored from weighted components: skills 40%, interests 20%, education 15%, projects 15%, experience 10%. Every result explains why.'],
  ['Is this a guarantee of a career outcome?', 'No. Scores are guidance estimates based on the information you provide.'],
  ['Which features work today?', 'Onboarding, career matching and skill-gap view. Roadmap, courses, resume, job match and CareerAI are marked as not yet configured.'],
]

export default function Landing() {
  const { dark, toggle } = useTheme()
  return (
    <div className="min-h-screen">
      <header className="mx-auto flex max-w-6xl items-center justify-between p-4">
        <div className="flex items-center gap-2 font-bold"><Sparkles className="text-indigo-500" size={20} />AI CareerGuide</div>
        <div className="flex items-center gap-2">
          <button aria-label="Toggle theme" className="btn-ghost !px-3" onClick={toggle}>{dark ? <Sun size={16} /> : <Moon size={16} />}</button>
          <Link to="/login" className="btn-ghost">Log in</Link><Link to="/register" className="btn">Sign up</Link>
        </div>
      </header>
      <section className="mx-auto max-w-4xl px-4 py-16 text-center md:py-24">
        <motion.h1 initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="bg-gradient-to-r from-indigo-600 to-violet-500 bg-clip-text text-4xl font-extrabold tracking-tight text-transparent md:text-6xl">Build the Career You’re Meant For.</motion.h1>
        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.15 }} className="mx-auto mt-5 max-w-2xl text-lg text-slate-600 dark:text-slate-400">AI-powered career guidance that analyzes your skills, interests, and goals to create a personalized career and learning roadmap.</motion.p>
        <Link to="/register" className="btn mt-8 !px-6 !py-3">Start Your Career Analysis</Link>
      </section>
      <section className="mx-auto grid max-w-6xl gap-4 px-4 sm:grid-cols-2 lg:grid-cols-3">
        {features.map(([I, t, d], i) => (
          <motion.div key={t} initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.05 }} className="card">
            <I className="mb-3 text-indigo-500" /><h3 className="font-semibold">{t}</h3><p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{d}</p>
          </motion.div>
        ))}
      </section>
      <section className="mx-auto max-w-6xl px-4 py-16">
        <h2 className="mb-6 text-center text-2xl font-bold">How it works</h2>
        <div className="grid gap-4 md:grid-cols-3">
          {['Tell us about your education, skills and interests', 'Get ranked career matches with clear reasons', 'Close your skill gaps with a focused plan'].map((s, i) => (
            <div key={s} className="card"><div className="mb-2 text-3xl font-extrabold text-indigo-500">{i + 1}</div>{s}</div>
          ))}
        </div>
      </section>
      <section className="mx-auto max-w-3xl px-4 pb-16">
        <h2 className="mb-4 text-center text-2xl font-bold">FAQ</h2>
        {faqs.map(([q, a]) => (<details key={q} className="card mb-2"><summary className="cursor-pointer font-medium">{q}</summary><p className="mt-2 text-sm text-slate-600 dark:text-slate-400">{a}</p></details>))}
      </section>
      <footer className="border-t border-slate-200 py-6 text-center text-sm text-slate-500 dark:border-slate-800">© {new Date().getFullYear()} AI CareerGuide. Guidance estimates, not guaranteed outcomes.</footer>
    </div>
  )
}
