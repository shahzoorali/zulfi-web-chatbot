(function(){
  function h(t, attrs, children){
    var el = document.createElement(t);
    attrs = attrs || {}; children = children || [];
    Object.keys(attrs).forEach(function(k){ if(el[k] !== undefined) el[k]=attrs[k]; else el.setAttribute(k, attrs[k]); });
    (Array.isArray(children)?children:[children]).forEach(function(c){ if(typeof c === 'string') el.appendChild(document.createTextNode(c)); else if(c) el.appendChild(c); });
    return el;
  }

  function init(root){
    var apiBase = root.getAttribute('data-api-base') || '';
    var apiKey = root.getAttribute('data-api-key') || '';
    var runId = root.getAttribute('data-run-id') || null;
    var title = root.getAttribute('data-title') || 'Chat with us';
    var color = root.getAttribute('data-color') || '#1452cc';

    var btn = h('button', { style: 'position:fixed;right:20px;bottom:20px;z-index:999999;background:'+color+';color:#fff;border:none;border-radius:24px;padding:12px 16px;cursor:pointer;box-shadow:0 6px 18px rgba(0,0,0,.2);' }, title);
    var panel = h('div', { style: 'position:fixed;right:20px;bottom:70px;width:360px;max-width:92vw;height:520px;max-height:80vh;background:#fff;border-radius:12px;box-shadow:0 12px 30px rgba(0,0,0,.25);display:none;flex-direction:column;overflow:hidden;z-index:999999;font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;' }, []);
    var header = h('div', { style: 'padding:12px 14px;background:'+color+';color:#fff;display:flex;justify-content:space-between;align-items:center;' }, [
      h('div', {}, title),
      h('button', { onclick: function(){ panel.style.display='none' }, style: 'background:transparent;border:none;color:#fff;font-size:18px;cursor:pointer;' }, '×')
    ]);
    var feed = h('div', { style: 'flex:1;padding:12px;overflow:auto;background:#f7f8fa;' });
    var inputWrap = h('div', { style: 'display:flex;gap:8px;padding:10px;border-top:1px solid #e9ecf1;background:#fff;' });
    var input = h('input', { type:'text', placeholder:'Type your question…', style:'flex:1;padding:10px 12px;border:1px solid #d8dde6;border-radius:8px;' });
    var send = h('button', { style: 'background:'+color+';color:#fff;border:none;padding:10px 14px;border-radius:8px;cursor:pointer;' }, 'Send');

    function addMsg(role, text){
      feed.appendChild(h('div', { style:'margin:8px 0;white-space:pre-wrap;word-break:break-word;' }, [
        h('div', { style:'font-size:12px;color:#6b7280;margin-bottom:2px;' }, role==='user'?'You':'Assistant'),
        h('div', { style:'background:'+(role==='user'?'#e5efff':'#fff')+';border:1px solid #e5e7eb;padding:10px;border-radius:8px;' }, text)
      ]));
      feed.scrollTop = feed.scrollHeight;
    }

    async function ask(q){
      addMsg('user', q);
      input.value = '';
      var thinking = h('div', { style:'font-size:12px;color:#6b7280;margin:8px 0;' }, 'Thinking…');
      feed.appendChild(thinking); feed.scrollTop = feed.scrollHeight;
      try{
        var res = await fetch((apiBase||'').replace(/\/$/,'') + '/answer', {
          method: 'POST',
          headers: Object.assign({ 'Content-Type': 'application/json' }, apiKey ? { 'X-API-Key': apiKey } : {}),
          body: JSON.stringify({ query: q, top_k: 3, run_id: runId })
        });
        var data = await res.json();
        feed.removeChild(thinking);
        addMsg('assistant', data.answer || 'No answer.');
        if(Array.isArray(data.sources) && data.sources.length){
          var s = data.sources.map(function(x){ return '• ' + (x.title || x.url || ''); }).join('\n');
          addMsg('assistant', 'Sources:\n'+s);
        }
      }catch(e){
        feed.removeChild(thinking);
        addMsg('assistant', 'Sorry, something went wrong.');
      }
    }

    send.onclick = function(){ if(input.value.trim()) ask(input.value.trim()); };
    input.addEventListener('keydown', function(e){ if(e.key==='Enter' && input.value.trim()) ask(input.value.trim()); });

    inputWrap.appendChild(input); inputWrap.appendChild(send);
    panel.appendChild(header); panel.appendChild(feed); panel.appendChild(inputWrap);
    btn.onclick = function(){ panel.style.display = (panel.style.display==='none' || !panel.style.display) ? 'flex' : 'none'; };

    document.body.appendChild(btn);
    document.body.appendChild(panel);
  }

  function start(){
    var scriptTags = document.querySelectorAll('script[src*="/embed.js"]');
    if(scriptTags.length){ init(scriptTags[0]); }
  }

  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})(); 