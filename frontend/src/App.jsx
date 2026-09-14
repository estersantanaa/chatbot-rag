import React, { useState, useEffect, useRef } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import ChatWindow from './components/ChatWindow';
import CloudSky from './components/CloudSky';
import SatinRibbon from './components/SatinRibbon';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const emptyByPersona = () => ({ cloud: [], clown: [] });
const emptyIdByPersona = () => ({ cloud: null, clown: null });
const trueByPersona = () => ({ cloud: true, clown: true });
const falseByPersona = () => ({ cloud: false, clown: false });

function App() {
  const [theme, setTheme] = useState('cloud');
  const [sessionsByPersona, setSessionsByPersona] = useState(emptyByPersona);
  const [activeByPersona, setActiveByPersona] = useState(emptyIdByPersona);
  const [homeByPersona, setHomeByPersona] = useState(trueByPersona);
  const [messagesByPersona, setMessagesByPersona] = useState(emptyByPersona);
  const [loadingByPersona, setLoadingByPersona] = useState(falseByPersona);
  const [uploading, setUploading] = useState(false);
  const [apiOnline, setApiOnline] = useState(false);
  const [ragReady, setRagReady] = useState(false);

  const activeByPersonaRef = useRef(activeByPersona);
  const loadingSessionRef = useRef({ cloud: null, clown: null });
  activeByPersonaRef.current = activeByPersona;

  const sessions = sessionsByPersona[theme];
  const activeSessionId = activeByPersona[theme];
  const messages = messagesByPersona[theme];
  const loading = loadingByPersona[theme];
  const homeView = homeByPersona[theme];

  useEffect(() => {
    document.body.className = theme === 'cloud' ? 'theme-cloud' : 'theme-clown';
  }, [theme]);

  useEffect(() => {
    bootstrapWorkspaces();
    checkRagHealth();
    const timer = setInterval(checkRagHealth, 4000);
    return () => clearInterval(timer);
  }, []);

  const checkRagHealth = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/health/rag`);
      if (res.ok) {
        const data = await res.json();
        setApiOnline(true);
        setRagReady(Boolean(data.ready_for_retrieval));
      } else {
        setApiOnline(false);
      }
    } catch (e) {
      setApiOnline(false);
    }
  };

  const listSessions = async (persona) => {
    const res = await fetch(`${API_BASE_URL}/sessions?persona=${persona}`);
    if (!res.ok) return [];
    return res.json();
  };

  const createSessionFor = async (persona) => {
    const res = await fetch(`${API_BASE_URL}/sessions?persona=${persona}`, {
      method: 'POST',
    });
    if (!res.ok) {
      throw new Error('Não foi possível criar a conversa.');
    }
    const newSession = await res.json();
    setSessionsByPersona((prev) => ({
      ...prev,
      [persona]: [newSession, ...prev[persona]],
    }));
    setActiveByPersona((prev) => ({ ...prev, [persona]: newSession.id }));
    setMessagesByPersona((prev) => ({ ...prev, [persona]: [] }));
    setHomeByPersona((prev) => ({ ...prev, [persona]: true }));
    setLoadingByPersona((prev) => ({ ...prev, [persona]: false }));
    return newSession;
  };

  const bootstrapWorkspaces = async () => {
    try {
      const [cloudSessions, clownSessions] = await Promise.all([
        listSessions('cloud'),
        listSessions('clown'),
      ]);
      const created = await fetch(`${API_BASE_URL}/sessions?persona=cloud`, {
        method: 'POST',
      });
      if (!created.ok) {
        setSessionsByPersona({ cloud: cloudSessions, clown: clownSessions });
        setApiOnline(true);
        return;
      }
      const session = await created.json();
      setSessionsByPersona({
        cloud: [session, ...cloudSessions],
        clown: clownSessions,
      });
      setActiveByPersona({ cloud: session.id, clown: null });
      setMessagesByPersona(emptyByPersona());
      setHomeByPersona(trueByPersona());
      setApiOnline(true);
    } catch (e) {
      console.error('Erro ao carregar sessões:', e);
      setApiOnline(false);
    }
  };

  const fetchMessages = async (sessionId, persona) => {
    try {
      const res = await fetch(`${API_BASE_URL}/sessions/${sessionId}/history`);
      if (!res.ok) return;
      const data = await res.json();
      if (activeByPersonaRef.current[persona] !== sessionId) return;
      setMessagesByPersona((prev) => ({ ...prev, [persona]: data }));
    } catch (e) {
      console.error('Erro ao carregar mensagens:', e);
    }
  };

  const handleSelectSession = (sessionId) => {
    const persona = theme;
    setHomeByPersona((prev) => ({ ...prev, [persona]: false }));
    setActiveByPersona((prev) => ({ ...prev, [persona]: sessionId }));
    setMessagesByPersona((prev) => ({ ...prev, [persona]: [] }));
    setLoadingByPersona((prev) => ({ ...prev, [persona]: false }));
    fetchMessages(sessionId, persona);
  };

  const handleGoHome = async () => {
    try {
      await createSessionFor(theme);
    } catch (e) {
      alert('Não foi possível conectar com o backend.');
    }
  };

  const handleCreateSession = async () => {
    try {
      await createSessionFor(theme);
    } catch (e) {
      alert('Não foi possível conectar com o backend.');
    }
  };

  const handleThemeChange = async (nextTheme) => {
    if (nextTheme === theme) return;
    setTheme(nextTheme);
    if (activeByPersona[nextTheme]) return;
    try {
      await createSessionFor(nextTheme);
    } catch (e) {
      alert('Não foi possível conectar com o backend.');
    }
  };

  const handleUpload = async (file) => {
    if (!file) return;
    setUploading(true);
    try {
      const form = new FormData();
      form.append('files', file);
      const res = await fetch(`${API_BASE_URL}/ingest`, { method: 'POST', body: form });
      const data = await res.json().catch(() => ({}));
      if (res.ok && data.success) {
        setRagReady(true);
        alert(`Documento indexado: ${file.name}`);
      } else {
        alert(data.message || data.detail || 'Falha ao indexar o arquivo.');
      }
    } catch (e) {
      alert('Não foi possível enviar o documento.');
    } finally {
      setUploading(false);
    }
  };

  const handleSendMessage = async (text) => {
    const persona = theme;
    const sessionId = activeByPersona[persona];
    if (!sessionId) return;

    setHomeByPersona((prev) => ({ ...prev, [persona]: false }));
    setMessagesByPersona((prev) => ({
      ...prev,
      [persona]: [
        ...prev[persona],
        {
          id: Date.now(),
          role: 'user',
          content: text,
          timestamp: new Date().toISOString(),
        },
      ],
    }));
    loadingSessionRef.current[persona] = sessionId;
    setLoadingByPersona((prev) => ({ ...prev, [persona]: true }));

    try {
      const res = await fetch(`${API_BASE_URL}/sessions/${sessionId}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: text, persona }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        const detail = typeof err.detail === 'string' ? err.detail : null;
        throw new Error(detail || `A API retornou ${res.status}`);
      }
      const data = await res.json();
      if (activeByPersonaRef.current[persona] !== sessionId) return;
      setMessagesByPersona((prev) => ({
        ...prev,
        [persona]: [
          ...prev[persona],
          {
            id: Date.now() + 1,
            role: 'assistant',
            content: data.response,
            sources: data.sources || [],
            timestamp: new Date().toISOString(),
          },
        ],
      }));
    } catch (e) {
      if (activeByPersonaRef.current[persona] !== sessionId) return;
      setMessagesByPersona((prev) => ({
        ...prev,
        [persona]: [
          ...prev[persona],
          {
            id: Date.now() + 2,
            role: 'assistant',
            content: e.message || 'Não consegui falar com a API. Confira se o backend está no ar.',
            timestamp: new Date().toISOString(),
          },
        ],
      }));
    } finally {
      if (loadingSessionRef.current[persona] === sessionId) {
        loadingSessionRef.current[persona] = null;
        setLoadingByPersona((prev) => ({ ...prev, [persona]: false }));
      }
    }
  };

  return (
    <>
      <div className="sky-layer">
        {theme === 'cloud' ? <CloudSky /> : <SatinRibbon />}
      </div>
      <div className="app-container">
        <Sidebar
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelectSession={handleSelectSession}
          onCreateSession={handleCreateSession}
          onUpload={handleUpload}
          uploading={uploading}
          apiOnline={apiOnline}
          ragReady={ragReady}
        />
        <main className="chat-shell">
          <Header
            theme={theme}
            onThemeChange={handleThemeChange}
            ragReady={ragReady}
            onGoHome={handleGoHome}
          />
          <ChatWindow
            key={`${theme}-${activeSessionId}`}
            messages={messages}
            activeSessionId={activeSessionId}
            loading={loading}
            theme={theme}
            homeView={homeView}
            onSendMessage={handleSendMessage}
          />
        </main>
      </div>
    </>
  );
}

export default App;
