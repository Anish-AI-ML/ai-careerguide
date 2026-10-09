import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './index.css'
if (localStorage.getItem('cg_theme') === 'dark') document.documentElement.classList.add('dark')
createRoot(document.getElementById('root')!).render(<StrictMode><App /></StrictMode>)
