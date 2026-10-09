import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { LayoutDashboard, Map, BookOpen, FileText, Briefcase, Bot, TrendingUp, LogOut, Moon, Sun, Sparkles, UserCog } from 'lucide-react'
import { useAuth } from '../lib/store'
import { useState } from 'react'

export const NAV = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/roadmap', label: 'Roadmap', icon: Map },
  { to: '/courses', label: 'Courses', icon: BookOpen },
  { to: '/resume', label: 'Resume', icon: FileText },
  { to: '/job-match', label: 'Job Match', icon: Briefcase },
  { to: '/careerai', label: 'CareerAI', icon: Bot },
  { to: '/progress', label: 'Progress', icon: TrendingUp },
]
export function useTheme() {
  const [dark, setDark] = useState(document.documentElement.classList.contains('dark'))
  const toggle = () => { const n = !dark; document.documentElement.classList.toggle('dark', n); localStorage.setItem('cg_theme', n ? 'dark' : 'light'); setDark(n) }
  return { dark, toggle }
}

export default function AppShell() {
  const { user, signOut } = useAuth(); const nav = useNavigate(); const { dark, toggle } = useTheme()
  return (
    <div className="min-h-screen md:flex">
      <aside className="border-b border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900 md:sticky md:top-0 md:h-screen md:w-60 md:border-b-0 md:border-r md:p-4">
        <div className="mb-3 flex items-center gap-2 px-2 font-bold md:mb-6"><Sparkles className="text-indigo-500" size={20} />AI CareerGuide</div>
        <nav className="flex gap-1 overflow-x-auto md:flex-col" aria-label="Main">
          {NAV.map(({ to, label, icon: I }) => (
            <NavLink key={to} to={to} className={({ isActive }) => `flex shrink-0 items-center gap-2 rounded-xl px-3 py-2 text-sm ${isActive ? 'bg-indigo-50 font-semibold text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300' : 'text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800'}`}><I size={16} />{label}</NavLink>
          ))}
        </nav>
        <div className="mt-4 hidden space-y-1 border-t border-slate-200 pt-4 dark:border-slate-800 md:block">
          <div className="px-2 pb-2 text-xs text-slate-500">{user?.name}<br />{user?.email}</div>
          <button className="btn-ghost w-full" onClick={() => nav('/onboarding')}><UserCog size={16} />Edit profile</button>
          <button className="btn-ghost w-full" onClick={toggle}>{dark ? <Sun size={16} /> : <Moon size={16} />}{dark ? 'Light' : 'Dark'} mode</button>
          <button className="btn-ghost w-full" onClick={() => { signOut(); nav('/') }}><LogOut size={16} />Log out</button>
        </div>
      </aside>
      <main className="min-w-0 flex-1 p-4 md:p-8"><Outlet /></main>
    </div>
  )
}
