import { jsx as _jsx } from "react/jsx-runtime";
import { createRoot } from 'react-dom/client';
import App from './App';
import './styles.css';
const rootEl = document.getElementById('root');
createRoot(rootEl).render(_jsx(App, {}));
