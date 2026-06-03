import { useState, useRef, useCallback } from 'react'

const API = 'http://localhost:8000'

const icons = {
  quill: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 4C14 4 8 8 6 18"/><path d="M6 18c1-3 3-5 6-6"/><path d="M6 18l-2 2"/>
    </svg>
  ),
  upload: (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
    </svg>
  ),
  file: (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
    </svg>
  ),
  trash: (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4h6v2"/>
    </svg>
  ),
  layers: (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>
    </svg>
  ),
  loader: (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ animation: 'spin 0.8s linear infinite' }}>
      <line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/>
      <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"/>
      <line x1="2" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="22" y2="12"/>
      <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"/><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"/>
    </svg>
  ),
}

export default function Sidebar({ open, documents, activeFilter, onFilterChange, onDocumentUploaded, onDocumentDeleted }) {
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const [deletingFile, setDeletingFile] = useState(null)
  const fileInputRef = useRef(null)

  const uploadFile = useCallback(async (file) => {
    if (!file?.name.endsWith('.pdf')) { setUploadError('Only PDF files are supported.'); return }
    setUploading(true); setUploadError(null)
    const form = new FormData()
    form.append('file', file)
    try {
      const res = await fetch(`${API}/documents/upload`, { method: 'POST', body: form })
      if (!res.ok) throw new Error((await res.json()).detail || 'Upload failed')
      const data = await res.json()
      onDocumentUploaded({ filename: data.filename, total_chunks: data.total_chunks, total_words: data.total_words })
    } catch (e) { setUploadError(e.message) }
    finally { setUploading(false) }
  }, [onDocumentUploaded])

  const deleteDoc = useCallback(async (filename, e) => {
    e.stopPropagation()
    setDeletingFile(filename)
    try {
      await fetch(`${API}/documents/${encodeURIComponent(filename)}`, { method: 'DELETE' })
      onDocumentDeleted(filename)
    } catch {}
    finally { setDeletingFile(null) }
  }, [onDocumentDeleted])

  const onDrop = useCallback((e) => {
    e.preventDefault(); setDragOver(false)
    const f = e.dataTransfer.files[0]; if (f) uploadFile(f)
  }, [uploadFile])

  const totalChunks = documents.reduce((s, d) => s + (d.total_chunks || 0), 0)

  return (
    <div style={{
      width: open ? 'var(--sidebar-w)' : '0',
      minWidth: open ? 'var(--sidebar-w)' : '0',
      overflow: 'hidden',
      transition: 'width 0.25s cubic-bezier(0.4,0,0.2,1), min-width 0.25s cubic-bezier(0.4,0,0.2,1)',
      background: 'var(--bg-surface)',
      borderRight: '1px solid var(--border)',
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      flexShrink: 0,
    }}>
      <div style={{ width: 'var(--sidebar-w)', display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>

        {/* Logo */}
        <div style={{ padding: '16px 14px 14px', borderBottom: '1px solid var(--border)', flexShrink: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
            <div style={{
              width: 28, height: 28, borderRadius: 7,
              background: 'var(--accent-muted)',
              border: '1px solid var(--accent-border)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: 'var(--accent)',
            }}>
              {icons.quill}
            </div>
            <div>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.3px', lineHeight: 1.2 }}>Quill</div>
              <div style={{ fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.2px' }}>Document intelligence</div>
            </div>
          </div>
        </div>

        {/* Upload zone */}
        <div style={{ padding: '10px', flexShrink: 0 }}>
          <div
            onDragOver={e => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={onDrop}
            onClick={() => !uploading && fileInputRef.current?.click()}
            style={{
              border: `1px dashed ${dragOver ? 'var(--accent)' : 'var(--border-md)'}`,
              borderRadius: 'var(--radius-md)',
              padding: '11px 12px',
              cursor: uploading ? 'default' : 'pointer',
              background: dragOver ? 'var(--accent-muted)' : 'transparent',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 7,
              color: dragOver ? 'var(--accent)' : uploading ? 'var(--text-muted)' : 'var(--text-secondary)',
              fontSize: 12,
              transition: 'all 0.15s',
            }}
          >
            {uploading ? icons.loader : icons.upload}
            <span>{uploading ? 'Indexing…' : 'Upload PDF'}</span>
          </div>
          <input ref={fileInputRef} type="file" accept=".pdf" style={{ display: 'none' }}
            onChange={e => { const f = e.target.files[0]; if (f) uploadFile(f); e.target.value = '' }} />
          {uploadError && (
            <div style={{ color: 'var(--red)', fontSize: 11, marginTop: 6, padding: '0 2px', lineHeight: 1.4 }}>{uploadError}</div>
          )}
        </div>

        {/* Nav */}
        {documents.length > 0 && (
          <div style={{ padding: '2px 10px 4px', flexShrink: 0 }}>
            <div
              onClick={() => onFilterChange(null)}
              style={{
                padding: '7px 10px',
                borderRadius: 'var(--radius-sm)',
                cursor: 'pointer',
                background: activeFilter === null ? 'var(--bg-active)' : 'transparent',
                border: activeFilter === null ? '1px solid var(--border-md)' : '1px solid transparent',
                display: 'flex', alignItems: 'center', gap: 8,
                transition: 'all 0.1s',
              }}
            >
              <span style={{ color: activeFilter === null ? 'var(--accent)' : 'var(--text-muted)' }}>{icons.layers}</span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 12, color: activeFilter === null ? 'var(--text-primary)' : 'var(--text-secondary)', fontWeight: activeFilter === null ? 500 : 400 }}>All documents</div>
                <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 1 }}>{documents.length} files · {totalChunks} chunks</div>
              </div>
            </div>
          </div>
        )}

        {/* Section header */}
        {documents.length > 0 && (
          <div style={{ padding: '8px 14px 4px', fontSize: 10, fontWeight: 600, letterSpacing: '0.7px', textTransform: 'uppercase', color: 'var(--text-faint)', flexShrink: 0 }}>
            Files
          </div>
        )}

        {/* Document list */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '0 10px 10px' }}>
          {documents.length === 0 && (
            <div style={{ padding: '24px 12px', textAlign: 'center' }}>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.6 }}>
                No documents yet.<br />Upload a PDF to get started.
              </div>
            </div>
          )}
          {documents.map(doc => (
            <DocRow
              key={doc.filename}
              doc={doc}
              active={activeFilter === doc.filename}
              deleting={deletingFile === doc.filename}
              onSelect={() => onFilterChange(activeFilter === doc.filename ? null : doc.filename)}
              onDelete={e => deleteDoc(doc.filename, e)}
            />
          ))}
        </div>

        {/* Footer stats */}
        {documents.length > 0 && (
          <div style={{ padding: '10px 14px', borderTop: '1px solid var(--border)', flexShrink: 0 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: 'var(--text-muted)' }}>
              <span>{documents.length} document{documents.length !== 1 ? 's' : ''}</span>
              <span>{totalChunks.toLocaleString()} chunks indexed</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function DocRow({ doc, active, deleting, onSelect, onDelete }) {
  const [hovered, setHovered] = useState(false)
  const name = doc.filename.replace(/\.pdf$/i, '')
  const short = name.length > 22 ? name.slice(0, 21) + '…' : name

  return (
    <div
      onClick={onSelect}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        padding: '7px 8px',
        borderRadius: 'var(--radius-sm)',
        cursor: 'pointer',
        background: active ? 'var(--bg-active)' : hovered ? 'var(--bg-hover)' : 'transparent',
        border: active ? '1px solid var(--border-md)' : '1px solid transparent',
        display: 'flex', alignItems: 'center', gap: 8,
        marginBottom: 1,
        transition: 'all 0.1s',
        animation: 'fadeIn 0.2s ease',
        opacity: deleting ? 0.4 : 1,
      }}
    >
      <div style={{
        width: 24, height: 24, borderRadius: 5, flexShrink: 0,
        background: active ? 'var(--accent-muted)' : 'var(--bg-elevated)',
        border: `1px solid ${active ? 'var(--accent-border)' : 'var(--border)'}`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: active ? 'var(--accent)' : 'var(--text-muted)',
        transition: 'all 0.1s',
      }}>
        {icons.file}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 12, color: active ? 'var(--text-primary)' : 'var(--text-secondary)', fontWeight: active ? 500 : 400, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {short}
        </div>
        <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 1 }}>{doc.total_chunks} chunks</div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 4, flexShrink: 0 }}>
        {!hovered && <div style={{ width: 5, height: 5, borderRadius: '50%', background: 'var(--green)', opacity: 0.7 }} />}
        {hovered && (
          <button
            onClick={onDelete}
            style={{
              color: 'var(--text-muted)', padding: '3px', borderRadius: 4,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              transition: 'color 0.1s',
            }}
            onMouseEnter={e => e.currentTarget.style.color = 'var(--red)'}
            onMouseLeave={e => e.currentTarget.style.color = 'var(--text-muted)'}
          >
            {icons.trash}
          </button>
        )}
      </div>
    </div>
  )
}