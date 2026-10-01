export function visibleUnfinishedSessions(items, currentSessionId) {
  return (items || []).filter((item) => item.session_id !== currentSessionId)
}

export function buildSessionUrl(currentHref, sessionId) {
  const url = new URL(currentHref)
  url.searchParams.set('session', sessionId)
  return url.toString()
}
