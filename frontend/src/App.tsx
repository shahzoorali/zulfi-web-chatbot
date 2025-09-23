import React, { useState } from 'react'
import { Chat } from './components/Chat'
import { Pipeline } from './components/Pipeline'

export default function App(){
  const [activeTab, setActiveTab] = useState<'chat' | 'pipeline'>('chat')
  
  return (
    <div className="container">
      <header className="header">
        <h1>Website Chatbot</h1>
        <nav className="nav-tabs">
          <button 
            className={`tab ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
          >
            Chat
          </button>
          <button 
            className={`tab ${activeTab === 'pipeline' ? 'active' : ''}`}
            onClick={() => setActiveTab('pipeline')}
          >
            Knowledge Base
          </button>
        </nav>
      </header>
      <main className="main">
        {activeTab === 'chat' ? <Chat /> : <Pipeline />}
      </main>
      <footer className="footer">
        <span>Powered by Astra DB + watsonx</span>
      </footer>
    </div>
  )
} 