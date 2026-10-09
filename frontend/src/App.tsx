import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import type { ReactNode } from 'react'
import { AuthProvider, useAuth } from './lib/store'
import AppShell from './layouts/AppShell'
import Landing from './pages/Landing'
import Auth from './pages/Auth'
import Onboarding from './pages/Onboarding'
import Dashboard from './pages/Dashboard'
import Courses from './pages/Courses'
import Roadmap from './pages/Roadmap'
import Resume from './pages/Resume'
import JobMatch from './pages/JobMatch'
import Chat from './pages/Chat'
import Progress from './pages/Progress'

const Protected = ({ children }: { children: ReactNode }) => {
  const { user, ready } = useAuth()
  if (!ready) return <div className="p-8 text-sm text-slate-500">Loading…</div>
  return user ? <>{children}</> : <Navigate to="/login" replace />
}
const NeedsProfile = ({ children }: { children: ReactNode }) => (useAuth().profile ? <>{children}</> : <Navigate to="/onboarding" replace />)

export default function App() {
  return (
    <AuthProvider><BrowserRouter><Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Auth mode="login" />} />
      <Route path="/register" element={<Auth mode="register" />} />
      <Route path="/onboarding" element={<Protected><Onboarding /></Protected>} />
      <Route element={<Protected><AppShell /></Protected>}>
        <Route path="/dashboard" element={<NeedsProfile><Dashboard /></NeedsProfile>} />
        <Route path="/courses" element={<Courses />} />
        <Route path="/roadmap" element={<Roadmap />} />
        <Route path="/resume" element={<Resume />} />
        <Route path="/job-match" element={<JobMatch />} />
        <Route path="/careerai" element={<Chat />} />
        <Route path="/progress" element={<Progress />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes></BrowserRouter></AuthProvider>
  )
}
