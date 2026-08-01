<script setup lang="ts">
import {
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogOverlay,
  AlertDialogPortal,
  AlertDialogRoot,
  AlertDialogTitle,
} from 'reka-ui';
import AppButton from '@/components/button/AppButton.vue';

const props = withDefaults(defineProps<{
  title: string;
  /** Body text. Overridden by the default slot if provided. */
  message?: string;
  confirmText?: string;
  cancelText?: string;
  confirmTone?: 'primary' | 'negative';
}>(), {
  confirmText: 'CONFIRM',
  cancelText: 'CANCEL',
  confirmTone: 'primary',
});

const emit = defineEmits<{
  confirm: [];
  cancel: [];
}>();

const open = defineModel<boolean>('open', { default: false });

const onConfirm = () => emit('confirm');
const onCancel = () => emit('cancel');
</script>

<template>
  <AlertDialogRoot v-model:open="open">
    <AlertDialogPortal>
      <AlertDialogOverlay
        class="overlay-root fixed inset-0 z-50 bg-black/60 backdrop-blur-sm"
      />
      <AlertDialogContent
        class="content-root fixed inset-x-0 bottom-0 z-50 sm:inset-0 sm:flex sm:items-center sm:justify-center sm:p-4 outline-none"
        @escape-key-down="onCancel"
      >
        <div class="panel w-full sm:max-w-md rounded-t-3xl sm:rounded-2xl shadow-black/40 bg-zinc-800 ring-1 ring-zinc-700 shadow-lg rounded-2xl p-3">
          <AlertDialogTitle class="text-xl font-bold">
            {{ props.title }}
          </AlertDialogTitle>
          <AlertDialogDescription
            v-if="props.message || $slots.default"
            as="div"
            class="mt-0.5 text-zinc-400 font-normal"
          >
            <slot>{{ props.message }}</slot>
          </AlertDialogDescription>
          <div class="mt-5 flex flex-col sm:flex-row sm:justify-end gap-3">
            <AlertDialogCancel as-child>
              <button
                class="w-full sm:w-auto px-5 py-2.5 rounded-2xl bg-zinc-700 text-zinc-100 transition-colors hover:bg-zinc-600 flex items-center justify-center uppercase"
                @click="onCancel"
              >
                {{ props.cancelText }}
              </button>
            </AlertDialogCancel>
            <AlertDialogAction as-child>
              <AppButton type="button" :tone="props.confirmTone" class="w-full sm:w-auto uppercase" @click="onConfirm">
                {{ props.confirmText }}
              </AppButton>
            </AlertDialogAction>
          </div>
        </div>
      </AlertDialogContent>
    </AlertDialogPortal>
  </AlertDialogRoot>
</template>

<style scoped>
/* Overlay fade */
.overlay-root[data-state='open'] {
  animation: overlay-fade-in 200ms ease-out;
}

.overlay-root[data-state='closed'] {
  animation: overlay-fade-out 160ms ease-in forwards;
}

/* Mobile: slide up / down from the bottom edge */
.content-root[data-state='open'] {
  animation: content-slide-up 240ms cubic-bezier(0.16, 1, 0.3, 1);
}

.content-root[data-state='closed'] {
  animation: content-slide-down 200ms ease-in forwards;
}

/* Desktop: centered fade */
@media (min-width: 640px) {
  .content-root[data-state='open'] {
    animation: content-fade-in 180ms ease-out;
  }

  .content-root[data-state='closed'] {
    animation: content-fade-out 160ms ease-in forwards;
  }
}

@keyframes overlay-fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes overlay-fade-out {
  from { opacity: 1; }
  to { opacity: 0; }
}

@keyframes content-slide-up {
  from { transform: translateY(100%); }
  to { transform: translateY(0); }
}

@keyframes content-slide-down {
  from { transform: translateY(0); }
  to { transform: translateY(100%); }
}

@keyframes content-fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes content-fade-out {
  from { opacity: 1; }
  to { opacity: 0; }
}
</style>