<script setup lang="ts">
import { Icon } from '@iconify/vue';
import {
  ToastClose,
  ToastDescription,
  ToastProvider,
  ToastRoot,
  ToastTitle,
  ToastViewport,
} from 'reka-ui';

defineOptions({
  inheritAttrs: false,
});

type SwipeDirection = 'right' | 'left' | 'up' | 'down';

const props = withDefaults(defineProps<{
  title: string;
  icon?: string;
  duration?: number;
  swipeDirection?: SwipeDirection;
}>(), {
  icon: 'material-symbols:notifications-rounded',
  duration: 5000,
  swipeDirection: 'right',
});

const open = defineModel<boolean>('open', {
  default: true,
});
</script>

<template>
  <ToastProvider
    label="Notification"
    :duration="props.duration"
    :disable-swipe="false"
    :swipe-direction="props.swipeDirection"
    :swipe-threshold="60"
  >
    <ToastRoot
      v-model:open="open"
      v-bind="$attrs"
      class="notification-root grid w-[calc(100vw-2rem)] max-w-md grid-cols-[auto_1fr_auto] items-start gap-3 rounded-2xl ring-1 ring-zinc-700 bg-zinc-800 p-3 text-white shadow-lg shadow-black/40 backdrop-blur-xl outline-none transition-transform data-[swipe=move]:translate-x-[var(--reka-toast-swipe-move-x)] data-[swipe=cancel]:translate-x-0 data-[swipe=end]:translate-x-[var(--reka-toast-swipe-end-x)] data-[swipe=move]:transition-none data-[swipe=cancel]:transition-transform data-[swipe=end]:transition-transform"
    >
      <div class="flex items-center justify-center w-10 h-10 p-2 rounded-lg bg-zinc-600/40 ring-1 ring-zinc-700">
        <slot name="icon">
          <Icon :icon="props.icon" class="h-5 w-5" />
        </slot>
      </div>

      <div class="min-w-0">
        <ToastTitle class="text-sm font-bold leading-5 text-zinc-50">
          {{ props.title }}
        </ToastTitle>
        <ToastDescription as="div" class="mt-1 text-sm font-medium leading-5 text-zinc-400">
          <slot />
        </ToastDescription>
      </div>

      <ToastClose
        aria-label="Dismiss notification"
        class="text-zinc-400 w-6 h-6 flex items-center justify-center hover:text-red-200 transition-all z-10 cursor-pointer bg-zinc-400/10 hover:bg-red-100/10 rounded-full"
      >
        <Icon icon="radix-icons:cross-2" class="h-4 w-4" />
      </ToastClose>
    </ToastRoot>

    <ToastViewport
      class="fixed bottom-4 right-4 z-50 flex max-h-dvh w-auto list-none flex-col gap-3 p-0 sm:bottom-6 sm:right-6"
    />
  </ToastProvider>
</template>

<style scoped>
.notification-root[data-state='closed'] {
  animation: notification-fade-out 180ms ease-in forwards;
}

@keyframes notification-fade-out {
  from {
    opacity: 1;
  }

  to {
    opacity: 0;
  }
}
</style>
