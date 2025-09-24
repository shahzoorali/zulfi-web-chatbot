import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import { Chat } from './components/Chat';
import { Pipeline } from './components/Pipeline';
export default function App() {
    const [activeTab, setActiveTab] = useState('chat');
    return (_jsxs("div", { className: "container", children: [_jsxs("header", { className: "header", children: [_jsx("h1", { children: "Website Chatbot" }), _jsxs("nav", { className: "nav-tabs", children: [_jsx("button", { className: `tab ${activeTab === 'chat' ? 'active' : ''}`, onClick: () => setActiveTab('chat'), children: "Chat" }), _jsx("button", { className: `tab ${activeTab === 'pipeline' ? 'active' : ''}`, onClick: () => setActiveTab('pipeline'), children: "Knowledge Base" })] })] }), _jsx("main", { className: "main", children: activeTab === 'chat' ? _jsx(Chat, {}) : _jsx(Pipeline, {}) }), _jsx("footer", { className: "footer", children: _jsx("span", { children: "Powered by Astra DB + watsonx" }) })] }));
}
