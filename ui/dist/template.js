function f({ apiUrl: s, wsUrl: r, fetchImpl: a = fetch }) {
  async function e() {
    const t = await a(s("/template"));
    if (!t.ok) throw new Error(`GET /template -> ${t.status}`);
    return t.json();
  }
  function c({ onOpen: t, onMessage: p, onClose: l } = {}) {
    const n = new WebSocket(r("/ws/echo"));
    t && n.addEventListener("open", t), p && n.addEventListener("message", (i) => p(JSON.parse(i.data))), l && n.addEventListener("close", l);
    let d = 0;
    return {
      send: (i) => n.send(JSON.stringify({ type: "aw_app_template_echo", data: i, id: String(d++) })),
      close: () => n.close(),
      raw: n
    };
  }
  return { template: e, connectEcho: c };
}
const o = "aw-app-template";
function w(s) {
  const a = f({
    apiUrl: (e) => `/api/apps/${o}${e}`,
    wsUrl: (e) => s.sdk.api.wsUrl(`/api/apps/${o}${e}`),
    fetchImpl: (e, c) => s.sdk.api.fetch(e, c)
  }).connectEcho({
    onMessage: (e) => console.debug(`[${o}] ws:`, e.type, e.data)
  });
  s.onDispose(() => a.close());
}
export {
  w as default,
  w as register
};
