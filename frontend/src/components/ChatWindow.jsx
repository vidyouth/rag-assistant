import { useState, useRef, useEffect, useCallback } from 'react'
import MessageBubble from './MessageBubble'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const icons = {
  send: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
    </svg>
  ),
  loader: (size = 14) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ animation: 'spin 0.8s linear infinite' }}>
      <line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/>
      <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"/>
      <line x1="2" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="22" y2="12"/>
      <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"/><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"/>
    </svg>
  ),
  sidebar: (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="18" height="18" rx="2"/><line x1="9" y1="3" x2="9" y2="21"/>
    </svg>
  ),
  warning: (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
    </svg>
  ),
  file: (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
    </svg>
  ),
}

function EmptyState({ documents }) {
  const prompts = [
    "What are the key findings?",
    "Summarize the main points",
    "What methodology was used?",
    "List the conclusions",
  ]
  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '40px 24px', gap: 28 }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.5px', marginBottom: 8 }}>
          {documents.length === 0 ? 'Start with a document' : 'Ask anything'}
        </div>
        <div style={{ fontSize: 13, color: 'var(--text-muted)', maxWidth: 320, lineHeight: 1.6 }}>
          {documents.length === 0
            ? 'Upload a PDF in the sidebar. Quill will index it and let you have a conversation with its contents.'
            : `${documents.length} document${documents.length > 1 ? 's' : ''} indexed and ready. Ask a question to get started.`}
        </div>
      </div>
      {documents.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, width: '100%', maxWidth: 420 }}>
          {prompts.map((p, i) => (
            <SuggestedPrompt key={i} text={p} />
          ))}
        </div>
      )}
    </div>
  )
}

function SuggestedPrompt({ text }) {
  const [hovered, setHovered] = useState(false)
  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        padding: '10px 13px',
        borderRadius: 'var(--radius-md)',
        border: `1px solid ${hovered ? 'var(--border-md)' : 'var(--border)'}`,
        background: hovered ? 'var(--bg-hover)' : 'var(--bg-elevated)',
        cursor: 'pointer',
        fontSize: 12,
        color: 'var(--text-secondary)',
        lineHeight: 1.4,
        transition: 'all 0.15s',
      }}
    >
      {text}
    </div>
  )
}

function TypingIndicator() {
  return (
    <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start', animation: 'fadeIn 0.2s ease' }}>
      <div style={{
        width: 26, height: 26, borderRadius: 7, flexShrink: 0,
        background: 'var(--accent-muted)',
        border: '1px solid var(--accent-border)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: 'var(--accent)',
      }}>
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M20 4C14 4 8 8 6 18"/><path d="M6 18c1-3 3-5 6-6"/><path d="M6 18l-2 2"/>
        </svg>
      </div>
      <div style={{
        background: 'var(--bg-elevated)',
        border: '1px solid var(--border)',
        borderRadius: '3px 12px 12px 12px',
        padding: '14px 16px',
        display: 'flex', gap: 5, alignItems: 'center',
      }}>
        {[0, 0.2, 0.4].map((delay, i) => (
          <div key={i} style={{
            width: 5, height: 5, borderRadius: '50%',
            background: 'var(--accent)',
            opacity: 0.4,
            animation: `bounce 1.1s ease-in-out ${delay}s infinite`,
          }} />
        ))}
      </div>
    </div>
  )
}

export default function ChatWindow({ messages, isLoading, activeFilter, documents, addMessage, setIsLoading, sidebarOpen, onToggleSidebar }) {
  const [input, setInput] = useState('')
  const [error, setError] = useState(null)
  const [focused, setFocused] = useState(false)
  const bottomRef = useRef(null)
  const textareaRef = useRef(null)

  const isOnlyWelcome = messages.length === 1 && messages[0].id === 'welcome'

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const autoResize = useCallback(() => {
    const ta = textareaRef.current
    if (!ta) return
    ta.style.height = 'auto'
    ta.style.height = Math.min(ta.scrollHeight, 160) + 'px'
  }, [])

  const sendMessage = useCallback(async () => {
    const question = input.trim()
    if (!question || isLoading) return
    setInput('')
    setError(null)
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
    addMessage({ role: 'user', content: question })
    setIsLoading(true)
    try {
      const res = await fetch(`${API}/chat/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            question,
            top_k: 5,
            filename_filter: activeFilter || null,
            similarity_threshold: 0.28,
            history: messages
                .filter(m => m.id !== 'welcome' && m.role !== undefined)
                .map(m => ({ role: m.role, content: m.content })),
}),
      })
      if (!res.ok) throw new Error((await res.json()).detail || 'Request failed')
      const data = await res.json()
      addMessage({ role: 'assistant', content: data.answer, sources: data.sources, had_context: data.had_context })
    } catch (e) {
      setError(e.message)
    } finally {
      setIsLoading(false)
    }
  }, [input, isLoading, activeFilter, addMessage, setIsLoading])

  const filterLabel = activeFilter
    ? (activeFilter.replace(/\.pdf$/i, '').length > 28 ? activeFilter.replace(/\.pdf$/i, '').slice(0, 27) + '…' : activeFilter.replace(/\.pdf$/i, ''))
    : 'all documents'

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden', minWidth: 0 }}>

      {/* Topbar */}
      <div style={{
        height: 50,
        borderBottom: '1px solid var(--border)',
        display: 'flex', alignItems: 'center',
        padding: '0 16px',
        gap: 10,
        flexShrink: 0,
        background: 'var(--bg-surface)',
      }}>
        <button
          onClick={onToggleSidebar}
          style={{
            width: 28, height: 28, borderRadius: 6,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: 'var(--text-muted)',
            background: 'transparent',
            transition: 'all 0.1s',
          }}
          onMouseEnter={e => { e.currentTarget.style.background = 'var(--bg-hover)'; e.currentTarget.style.color = 'var(--text-secondary)' }}
          onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--text-muted)' }}
        >
          {icons.sidebar}
        </button>

        <div style={{ width: 1, height: 16, background: 'var(--border)', flexShrink: 0 }} />

        {activeFilter ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
            <span style={{ color: 'var(--text-muted)' }}>{icons.file}</span>
            <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{filterLabel}</span>
          </div>
        ) : (
          <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
            {documents.length > 0
              ? <span>Searching across <span style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>{documents.length} document{documents.length > 1 ? 's' : ''}</span></span>
              : <span style={{ color: 'var(--text-muted)' }}>No documents indexed</span>
            }
          </div>
        )}

        <div style={{ marginLeft: 'auto', fontSize: 10, color: 'var(--text-muted)', background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: 4, padding: '3px 7px', fontWeight: 500, letterSpacing: '0.2px' }}>
          GPT-4o mini
        </div>
      </div>

      {/* Messages or empty state */}
      <div style={{ flex: 1, overflowY: 'auto', padding: isOnlyWelcome ? '0' : '28px 28px 12px' }}>
        {isOnlyWelcome ? (
          <EmptyState documents={documents} />
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 22, maxWidth: 760, margin: '0 auto' }}>
            {messages.filter(m => m.id !== 'welcome').map(msg => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            {isLoading && <TypingIndicator />}
            {error && (
              <div style={{
                display: 'flex', alignItems: 'flex-start', gap: 8,
                color: 'var(--red)', fontSize: 13,
                padding: '10px 14px',
                background: 'var(--red-dim)',
                border: '1px solid rgba(248,113,113,0.15)',
                borderRadius: 'var(--radius-md)',
              }}>
                {icons.warning}
                <span>{error}</span>
              </div>
            )}
            <div ref={bottomRef} style={{ height: 4 }} />
          </div>
        )}
      </div>

      {/* Input */}
      <div style={{ padding: '10px 20px 18px', flexShrink: 0, background: 'var(--bg-base)' }}>
        <div style={{ maxWidth: 760, margin: '0 auto' }}>
          <div style={{
            display: 'flex', alignItems: 'flex-end', gap: 8,
            background: 'var(--bg-input)',
            border: `1px solid ${focused ? 'var(--border-strong)' : 'var(--border-md)'}`,
            borderRadius: 'var(--radius-xl)',
            padding: '10px 10px 10px 16px',
            transition: 'border-color 0.15s',
          }}>
            <textarea
              ref={textareaRef}
              value={input}
              rows={1}
              onChange={e => { setInput(e.target.value); autoResize() }}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() } }}
              onFocus={() => setFocused(true)}
              onBlur={() => setFocused(false)}
              placeholder={`Ask about ${filterLabel}…`}
              style={{
                flex: 1, background: 'transparent', border: 'none', outline: 'none',
                color: 'var(--text-primary)', fontSize: 13.5, lineHeight: 1.5,
                resize: 'none', fontFamily: 'inherit', overflowY: 'hidden',
                paddingBottom: 2,
              }}
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim() || isLoading}
              style={{
                width: 32, height: 32, borderRadius: 10, flexShrink: 0,
                background: input.trim() && !isLoading ? 'var(--accent)' : 'var(--bg-hover)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                cursor: input.trim() && !isLoading ? 'pointer' : 'not-allowed',
                color: input.trim() && !isLoading ? '#fff' : 'var(--text-muted)',
                transition: 'all 0.15s',
              }}
            >
              {isLoading ? icons.loader(14) : icons.send}
            </button>
          </div>
          <div style={{ textAlign: 'center', fontSize: 10, color: 'var(--text-faint)', marginTop: 7, letterSpacing: '0.2px' }}>
            Quill · answers grounded in your documents · shift+enter for new line
          </div>
        </div>
      </div>
    </div>
  )
}