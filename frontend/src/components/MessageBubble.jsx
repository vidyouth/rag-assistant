import ReactMarkdown from 'react-markdown'

const icons = {
  quill: (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 4C14 4 8 8 6 18"/><path d="M6 18c1-3 3-5 6-6"/><path d="M6 18l-2 2"/>
    </svg>
  ),
  source: (
    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
    </svg>
  ),
}

function scoreColor(score) {
  if (score >= 0.72) return 'var(--green)'
  if (score >= 0.5) return 'var(--amber)'
  return 'var(--text-muted)'
}

function truncateFilename(name, max = 22) {
  const stripped = name.replace(/\.pdf$/i, '')
  return stripped.length > max ? stripped.slice(0, max - 1) + '…' : stripped
}

export default function MessageBubble({ message }) {
  if (message.role === 'user') {
    return (
      <div style={{ display: 'flex', justifyContent: 'flex-end', animation: 'fadeIn 0.2s ease' }}>
        <div style={{
          background: 'var(--accent)',
          color: '#fff',
          borderRadius: '12px 12px 3px 12px',
          padding: '10px 14px',
          maxWidth: '72%',
          fontSize: 13.5,
          lineHeight: 1.6,
          fontWeight: 400,
        }}>
          {message.content}
        </div>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', gap: 10, maxWidth: '84%', animation: 'fadeIn 0.25s ease' }}>
      <div style={{
        width: 26, height: 26, borderRadius: 7, flexShrink: 0, marginTop: 1,
        background: 'var(--accent-muted)',
        border: '1px solid var(--accent-border)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: 'var(--accent)',
      }}>
        {icons.quill}
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border)',
          borderRadius: '3px 12px 12px 12px',
          padding: '13px 16px',
        }}>
          <div className="md-body">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        </div>

        {message.sources?.length > 0 && (
          <div style={{ marginTop: 8, display: 'flex', flexWrap: 'wrap', gap: 5 }}>
            {message.sources.map((s, i) => (
              <div key={i} style={{
                display: 'inline-flex', alignItems: 'center', gap: 5,
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border)',
                borderRadius: 5,
                padding: '4px 8px',
                fontSize: 11,
                color: 'var(--text-muted)',
                transition: 'border-color 0.15s',
                cursor: 'default',
              }}
              onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--border-strong)'}
              onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
              >
                <span style={{ color: 'var(--text-muted)', opacity: 0.7 }}>{icons.source}</span>
                <span style={{ color: 'var(--accent-text)', fontWeight: 500 }}>{truncateFilename(s.filename)}</span>
                <span style={{ color: 'var(--text-faint)', fontSize: 10 }}>·</span>
                <span style={{ color: 'var(--text-muted)', fontSize: 10 }}>chunk {s.chunk_index}</span>
                <span style={{
                  background: 'var(--bg-hover)',
                  color: scoreColor(s.similarity_score),
                  fontSize: 10, fontWeight: 600,
                  padding: '1px 5px', borderRadius: 3,
                  fontVariantNumeric: 'tabular-nums',
                }}>
                  {Math.round(s.similarity_score * 100)}%
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}