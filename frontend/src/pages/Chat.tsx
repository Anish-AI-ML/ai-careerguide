import { useEffect, useRef, useState } from 'react'
import { Bot, Plus, Send, Trash2, User } from 'lucide-react'
import { api, type ChatMsg, type ChatSessionItem } from '../lib/api'

export default function Chat() {
  const [sessions, setSessions] = useState<ChatSessionItem[]>([]); const [sid, setSid] = useState<string | null>(null)
  const [msgs, setMsgs] = useState<ChatMsg[]>([]); const [input, setInput] = useState(''); const [busy, setBusy] = useState(false)
  const [err, setErr] = useState(''); const [prompts, setPrompts] = useState<string[]>([]); const [mode, setMode] = useState('')
  const end = useRef<HTMLDivElement>(null)
  const loadSessions = () => api.chatSessions().then(setSessions).catch(() => {})
  useEffect(() => { loadSessions(); api.chatSuggestions().then(setPrompts).catch(() => {}) }, [])
  useEffect(() => { end.current?.scrollIntoView({ behavior: 'smooth' }) }, [msgs, busy])

  async function open(id: string) { setErr(''); setSid(id); try { setMsgs(await api.chatMessages(id)) } catch (e) { setErr(e instanceof Error ? e.message : 'Could not load chat') } }
  const fresh = () => { setSid(null); setMsgs([]); setErr('') }

  async function send(text: string) {
    const t = text.trim(); if (!t || busy) return
    setErr(''); setInput(''); setBusy(true); setMsgs(m => [...m, { role: 'user', content: t }])
    try {
      const r = await api.chat(t, sid)
      setMsgs(m => [...m, { role: 'assistant', content: r.reply }]); setMode(r.mode)
      if (!sid) { setSid(r.session_id); loadSessions() }
    } catch (e) { setErr(e instanceof Error ? e.message : 'Something went wrong') } finally { setBusy(false) }
  }
  async function clear() {
    if (!sid) return fresh()
    if (!window.confirm('Delete this conversation? This cannot be undone.')) return
    try { await api.deleteChat(sid); fresh(); loadSessions() } catch (e) { setErr(e instanceof Error ? e.message : 'Could not delete') }
  }

  return (
    <div className="mx-auto flex h-[calc(100vh-6rem)] max-w-5xl gap-4">
      <aside className="card hidden w-56 shrink-0 flex-col gap-2 overflow-y-auto md:flex">
        <button className="btn" onClick={fresh}><Plus size={14} />New chat</button>
        <div className="mt-2 text-xs font-semibold uppercase text-slate-500">History</div>
        {!sessions.length && <p className="text-xs text-slate-500">No conversations yet.</p>}
        {sessions.map(s => <button key={s.id} onClick={() => open(s.id)} className={`truncate rounded-lg px-2 py-1.5 text-left text-sm ${s.id === sid ? 'bg-indigo-50 font-medium text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300' : 'hover:bg-slate-100 dark:hover:bg-slate-800'}`}>{s.title}</button>)}
      </aside>
      <section className="card flex min-w-0 flex-1 flex-col !p-0">
        <header className="flex items-center justify-between border-b border-slate-200 px-4 py-3 dark:border-slate-800">
          <div className="flex items-center gap-2 font-semibold"><Bot className="text-indigo-500" size={18} />CareerAI{mode && <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-normal text-slate-500 dark:bg-slate-800">{mode === 'llm' ? 'AI model' : 'built-in assistant'}</span>}</div>
          <div className="flex gap-2"><button className="btn-ghost !px-3 md:hidden" onClick={fresh} aria-label="New chat"><Plus size={14} /></button><button className="btn-ghost !px-3" onClick={clear}><Trash2 size={14} />Clear chat</button></div>
        </header>
        <div className="flex-1 space-y-3 overflow-y-auto p-4" aria-live="polite">
          {!msgs.length && <div className="text-center text-sm text-slate-500"><Bot className="mx-auto mb-2 text-indigo-500" />Ask me about careers, skills, roadmaps, projects or your resume.</div>}
          {msgs.map((m, i) => (
            <div key={i} className={`flex gap-2 ${m.role === 'user' ? 'flex-row-reverse' : ''}`}>
              <div className={`mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${m.role === 'user' ? 'bg-indigo-600 text-white' : 'bg-slate-200 dark:bg-slate-700'}`}>{m.role === 'user' ? <User size={14} /> : <Bot size={14} />}</div>
              <div className={`max-w-[80%] whitespace-pre-wrap rounded-2xl px-3 py-2 text-sm ${m.role === 'user' ? 'bg-indigo-600 text-white' : 'bg-slate-100 dark:bg-slate-800'}`}>{m.content}</div>
            </div>))}
          {busy && <div className="flex gap-2" role="status" aria-label="CareerAI is typing"><div className="mt-1 flex h-7 w-7 items-center justify-center rounded-full bg-slate-200 dark:bg-slate-700"><Bot size={14} /></div>
            <div className="flex items-center gap-1 rounded-2xl bg-slate-100 px-3 py-3 dark:bg-slate-800">{[0, 1, 2].map(d => <span key={d} className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400" style={{ animationDelay: `${d * 0.15}s` }} />)}</div></div>}
          <div ref={end} />
        </div>
        {err && <p role="alert" className="px-4 pb-2 text-sm text-red-500">{err}</p>}
        <div className="border-t border-slate-200 p-3 dark:border-slate-800">
          <div className="mb-2 flex gap-2 overflow-x-auto pb-1">{prompts.map(p => <button key={p} disabled={busy} onClick={() => send(p)} className="shrink-0 rounded-full border border-slate-300 px-3 py-1 text-xs hover:bg-slate-100 disabled:opacity-50 dark:border-slate-700 dark:hover:bg-slate-800">{p}</button>)}</div>
          <form className="flex gap-2" onSubmit={e => { e.preventDefault(); send(input) }}>
            <input className="input" maxLength={1000} placeholder="Ask CareerAI…" value={input} onChange={e => setInput(e.target.value)} aria-label="Message" />
            <button className="btn" disabled={busy || !input.trim()} aria-label="Send"><Send size={16} /></button>
          </form>
          <p className="mt-2 text-center text-xs text-slate-500">Guidance only, not guaranteed outcomes.</p>
        </div>
      </section>
    </div>
  )
}
