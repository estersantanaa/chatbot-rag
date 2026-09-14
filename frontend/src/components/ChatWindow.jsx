import React, { useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Send } from 'lucide-react';

const SUGGESTIONS = [
  { title: 'Quem é a Ester Santana?', prompt: 'Quem é a Ester Santana?' },
  { title: 'Qual a stack desse chatbot RAG?', prompt: 'Qual a stack desse chatbot RAG?' },
  { title: 'Quais assuntos estão ingeridos na base?', prompt: 'Quais assuntos estão ingeridos na base?' },
];

function AssistantMarkdown({ content }) {
  return (
    <div className="markdown-body">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ href, children }) => (
            <a href={href} target="_blank" rel="noreferrer noopener">
              {children}
            </a>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

function ChatWindow({ messages, activeSessionId, loading, theme, homeView, onSendMessage }) {
  const [input, setInput] = React.useState('');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    onSendMessage(input);
    setInput('');
  };

  return (
    <div className="chat-container">
      <div className="messages-viewport">
        {homeView ? (
          <div className="empty-state">
            <h3 className="empty-title">
              {theme === 'cloud' ? 'Bem vindo a comunicação sempre nas nuvens :)' : 'Pergunte à base, com um pouco de circo.'}
            </h3>
            <div className="card-grid">
              {SUGGESTIONS.map((card) => (
                <button
                  key={card.title}
                  type="button"
                  className="suggested-card"
                  onClick={() => !loading && onSendMessage(card.prompt)}
                >
                  <span className="suggested-title">{card.title}</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div key={msg.id} className={`message-row ${msg.role === 'user' ? 'user' : 'assistant'}`}>
              <div className="message-bubble">
                {msg.role === 'assistant' ? (
                  <AssistantMarkdown content={msg.content} />
                ) : (
                  <div className="user-message-text">{msg.content}</div>
                )}
                {msg.role === 'assistant' && msg.sources?.length > 0 && (
                  <div className="message-sources">
                    {msg.sources.map((source, idx) => (
                      <div key={`${source.source}-${idx}`} className="source-item">
                        <strong>{source.source}</strong>
                        {source.excerpt ? ` — ${source.excerpt}` : ''}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))
        )}

        {loading && !homeView && (
          <div className="message-row assistant">
            <div className="message-bubble">
              <div className="typing-indicator">
                <div className="typing-dot" />
                <div className="typing-dot" />
                <div className="typing-dot" />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {!homeView && (
      <form className="chat-input-bar" onSubmit={handleSubmit}>
        <div className="input-wrapper">
          <input
            type="text"
            className="chat-input"
            placeholder={activeSessionId ? 'Pergunte sobre a ClownorCloud' : 'Aguarde a conversa iniciar…'}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={!activeSessionId || loading}
          />
          <button
            type="submit"
            className="send-btn"
            disabled={!activeSessionId || !input.trim() || loading}
          >
            <Send size={16} />
          </button>
        </div>
      </form>
      )}
    </div>
  );
}

export default ChatWindow;
