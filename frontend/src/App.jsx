import { useState, useCallback, useEffect } from 'react'
import Sidebar from './components/Sidebar'
import ChatWindow from './components/ChatWindow'
import './index.css'

const API = 'http://localhost:8000'

const WELCOME = {
  id: 'welcome',
  role: 'assistant',
  content: "I'm ready to help you explore your documents. Upload a PDF using the sidebar and I'll index it — then ask me anything. I'll always show you exactly where each answer came from.",
  sources: [],
}

export default function App() {
  const [documents, setDocuments] = useState([])
  const [messages, setMessages] = useState([WELCOME])
  const [isLoading, setIsLoading] = useState(false)
  const [activeFilter, setActiveFilter] = useState(null)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [docsLoading, setDocsLoading] = useState(true)

  // Load existing documents from backend on startup
  useEffect(() => {
    async function loadDocuments() {
      try {
        const res = await fetch(`${API}/documents/list`)
        if (!res.ok) return
        const data = await res.json()
        const docs = data.documents
          .filter(d => d.indexed)
          .map(d => ({ filename: d.filename, total_chunks: d.total_chunks, total_words: null }))
        setDocuments(docs)
      } catch (e) {
        console.error('Failed to load documents:', e)
      } finally {
        setDocsLoading(false)
      }
    }
    loadDocuments()
  }, [])

  const addMessage = useCallback((msg) => {
    setMessages(prev => [...prev, { id: `${Date.now()}-${Math.random()}`, ...msg }])
  }, [])

  const handleDocumentUploaded = useCallback((doc) => {
    setDocuments(prev => {
      if (prev.find(d => d.filename === doc.filename)) return prev
      return [...prev, doc]
    })
  }, [])

  const handleDocumentDeleted = useCallback((filename) => {
    setDocuments(prev => prev.filter(d => d.filename !== filename))
    setActiveFilter(prev => prev === filename ? null : prev)
  }, [])

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw', overflow: 'hidden', background: 'var(--bg-base)' }}>
      <Sidebar
        open={sidebarOpen}
        documents={documents}
        docsLoading={docsLoading}
        activeFilter={activeFilter}
        onFilterChange={setActiveFilter}
        onDocumentUploaded={handleDocumentUploaded}
        onDocumentDeleted={handleDocumentDeleted}
      />
      <ChatWindow
        messages={messages}
        isLoading={isLoading}
        activeFilter={activeFilter}
        documents={documents}
        addMessage={addMessage}
        setIsLoading={setIsLoading}
        sidebarOpen={sidebarOpen}
        onToggleSidebar={() => setSidebarOpen(o => !o)}
      />
    </div>
  )
}