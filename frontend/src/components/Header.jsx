import React from 'react';

function Header({ theme, onThemeChange, ragReady, onGoHome }) {
  return (
    <header className="chat-header">
      <div>
        <h2 className="header-title">Documentação ClownorCloud</h2>
        <span className="header-status">
          {ragReady ? 'Respostas com base nos documentos indexados' : 'Indexando a base… a primeira subida pode levar um minuto'}
        </span>
      </div>

      <div className="header-actions">
        <button type="button" className="home-btn" onClick={onGoHome}>
          Voltar
        </button>
        <div className="theme-selector">
          <button
            type="button"
            className={`theme-toggle-btn ${theme === 'cloud' ? 'active' : ''}`}
            onClick={() => onThemeChange('cloud')}
          >
            Cloud
          </button>
          <button
            type="button"
            className={`theme-toggle-btn ${theme === 'clown' ? 'active' : ''}`}
            onClick={() => onThemeChange('clown')}
          >
            Clown
          </button>
        </div>
      </div>
    </header>
  );
}

export default Header;
