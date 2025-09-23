import React, { useState } from 'react'
import { Chat } from './components/Chat'

export default function App(){
  const [query, setQuery] = useState('')
  return (
    <div className="container">
      <header className="header">
        <h1>Website Chatbot</h1>
      </header>
      <main className="main">
        <Chat />
      </main>
      <footer className="footer">
        <span>Powered by Astra DB + watsonx</span>
      </footer>
    </div>
  )
} 