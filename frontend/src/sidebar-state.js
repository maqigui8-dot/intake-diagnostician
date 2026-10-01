export const SIDEBAR_STORAGE_KEY = 'intake-sidebar-collapsed'

export function readSidebarCollapsed(storage) {
  try {
    return storage?.getItem(SIDEBAR_STORAGE_KEY) === 'true'
  } catch {
    return false
  }
}

export function writeSidebarCollapsed(storage, collapsed) {
  try {
    storage?.setItem(SIDEBAR_STORAGE_KEY, String(Boolean(collapsed)))
  } catch {
    // The layout must remain usable when storage is blocked or unavailable.
  }
}
