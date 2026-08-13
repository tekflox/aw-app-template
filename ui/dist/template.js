function f({ apiUrl: n, wsUrl: a, fetchImpl: o = fetch }) {
  async function r() {
    const t = await o(n("/hello"));
    if (!t.ok) throw new Error(`GET /hello -> ${t.status}`);
    return t.json();
  }
  function e({ onOpen: t, onMessage: s, onClose: u } = {}) {
    const c = new WebSocket(a("/ws/echo"));
    return t && c.addEventListener("open", t), s && c.addEventListener("message", (l) => s(l.data)), u && c.addEventListener("close", u), {
      send: (l) => c.send(l),
      close: () => c.close(),
      raw: c
    };
  }
  return { hello: r, connectEcho: e };
}
const i = "hello";
function p(n) {
  const a = f({
    apiUrl: (e) => `/api/apps/${i}${e}`,
    wsUrl: (e) => n.sdk.api.wsUrl(`/api/apps/${i}${e}`),
    fetchImpl: (e, t) => n.sdk.api.fetch(e, t)
  });
  function o() {
    const [e, t] = n.React.useState("…");
    return n.React.useEffect(() => {
      a.hello().then((s) => t(s.message)).catch((s) => t(`error: ${s.message}`));
    }, []), n.h("span", { title: e }, "template");
  }
  n.registerSlot("core.nav", o);
  const r = a.connectEcho({
    onMessage: (e) => console.debug(`[${i}] echo:`, e)
  });
  n.onDispose(() => r.close());
}
export {
  p as default,
  p as register
};
