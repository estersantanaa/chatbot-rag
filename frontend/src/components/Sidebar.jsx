import React, { useRef } from 'react';

function Sidebar({
  sessions,
  activeSessionId,
  onSelectSession,
  onCreateSession,
  onUpload,
  uploading,
  apiOnline,
  ragReady,
}) {
  const fileInputRef = useRef(null);

  const formatDate = (dateString) => {
    try {
      return new Date(dateString).toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: 'short',
      });
    } catch (e) {
      return '';
    }
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div>
          <h1 className="logo-text">ClownorCloud</h1>
          <span className="logo-kicker">Assistente da documentação</span>
        </div>

        <button className="new-chat-btn" onClick={onCreateSession}>
          Nova conversa
        </button>

        <input
          ref={fileInputRef}
          type="file"
          accept=".txt,.pdf"
          hidden
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) onUpload(file);
            e.target.value = '';
          }}
        />
        <button
          className="upload-btn"
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
        >
          {uploading ? 'Indexando…' : 'Adicionar PDF ou TXT'}
        </button>
      </div>

      <div className="sidebar-sessions">
        {sessions.map((session) => (
          <button
            key={session.id}
            className={`session-item ${activeSessionId === session.id ? 'active' : ''}`}
            onClick={() => onSelectSession(session.id)}
          >
            <span className="session-title">Conversa {session.id}</span>
            <span className="session-date">{formatDate(session.created_at)}</span>
          </button>
        ))}
      </div>

      <div className="sidebar-footer">
        <span className={`status-dot ${!apiOnline ? 'offline' : ragReady ? '' : 'pending'}`} />
        {!apiOnline && 'API offline'}
        {apiOnline && !ragReady && 'Indexando documentos'}
        {apiOnline && ragReady && 'Base pronta'}
      </div>
    </aside>
  );
}

export default Sidebar;
