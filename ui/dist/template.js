function f({ apiUrl: c, wsUrl: a, fetchImpl: s = fetch }) {
  async function e() {
    const n = await s(c("/hello"));
    if (!n.ok) throw new Error(`GET /hello -> ${n.status}`);
    return n.json();
  }
  function o({ onOpen: n, onMessage: l, onClose: d } = {}) {
    const t = new WebSocket(a("/ws/echo"));
    return n && t.addEventListener("open", n), l && t.addEventListener("message", (i) => l(i.data)), d && t.addEventListener("close", d), {
      send: (i) => t.send(i),
      close: () => t.close(),
      raw: t
    };
  }
  return { hello: e, connectEcho: o };
}
const r = "hello";
function p(c) {
  const s = f({
    apiUrl: (e) => `/api/apps/${r}${e}`,
    wsUrl: (e) => c.sdk.api.wsUrl(`/api/apps/${r}${e}`),
    fetchImpl: (e, o) => c.sdk.api.fetch(e, o)
  }).connectEcho({
    onMessage: (e) => console.debug(`[${r}] echo:`, e)
  });
  c.onDispose(() => s.close());
}
export {
  p as default,
  p as register
};
