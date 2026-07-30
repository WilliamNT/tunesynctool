import { ref } from 'vue';

export interface AppNotificationOptions {
  /** Bold title line of the toast. */
  title: string;
  /** Optional description text shown below the title. */
  description?: string;
  /** Iconify icon name for the leading icon. */
  icon?: string;
  /** Time in ms before the toast auto-dismisses. Defaults to 5000. */
  duration?: number;
}

export interface AppNotificationItem extends AppNotificationOptions {
  id: number;
}

// Module-level singleton so every caller of useAppNotification() shares the
// same toast queue, which is rendered once at the app root.
const toasts = ref<AppNotificationItem[]>([]);
let nextId = 0;

export function useAppNotification() {
  /**
   * Push a toast. The toast auto-dismisses after `duration` (or when the user
   * swipes / closes it) — the root renderer handles removal, so callers only
   * need to call this and do nothing else.
   * Returns the toast id, which can be passed to `dismiss` for manual removal.
   */
  function notify(options: AppNotificationOptions): number {
    const id = nextId++;
    toasts.value.push({ id, ...options });
    return id;
  }

  function dismiss(id: number) {
    const index = toasts.value.findIndex(toast => toast.id === id);
    if (index !== -1) {
      toasts.value.splice(index, 1);
    }
  }

  function dismissAll() {
    toasts.value.splice(0, toasts.value.length);
  }

  return { toasts, notify, dismiss, dismissAll };
}