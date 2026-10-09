import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { api, ApiError, getToken, setToken, type ApiUser } from './api'

export type Profile = {
  degree: string; branch: string; institution: string; year: string; cgpa: string
  skills: string[]; interests: string[]; projects: string; certifications: string
  experience: string; goal: string
}
export const emptyProfile: Profile = { degree: '', branch: '', institution: '', year: '', cgpa: '', skills: [], interests: [], projects: '', certifications: '', experience: '', goal: '' }

type Ctx = { user: ApiUser | null; profile: Profile | null; ready: boolean; signIn: (token: string, u: ApiUser) => Promise<Profile | null>; signOut: () => void; setProfile: (p: Profile) => void }
const C = createContext<Ctx>(null!)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<ApiUser | null>(null)
  const [profile, setProfile] = useState<Profile | null>(null)
  const [ready, setReady] = useState(!getToken())
  const signOut = () => { setToken(null); setUser(null); setProfile(null) }

  useEffect(() => {
    if (!getToken()) return
    Promise.all([api.me(), api.getProfile()])
      .then(([u, p]) => { setUser(u); setProfile(p) })
      .catch(e => { if (e instanceof ApiError && e.status === 401) signOut() })
      .finally(() => setReady(true))
  }, [])

  const signIn: Ctx['signIn'] = async (token, u) => {
    setToken(token); setUser(u)
    const p = await api.getProfile().catch(() => null)
    setProfile(p); return p
  }
  return <C.Provider value={{ user, profile, ready, signIn, signOut, setProfile }}>{children}</C.Provider>
}
export const useAuth = () => useContext(C)
