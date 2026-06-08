<script setup lang="ts">
import { SwitchRoot, SwitchThumb } from 'reka-ui';

withDefaults(defineProps<{
  id?: string;
  label: string;
  description?: string;
  disabled?: boolean;
}>(), {
  disabled: false,
});

const model = defineModel<boolean>({
  default: false,
});
</script>

<template>
  <div class="flex items-center gap-3 rounded-xl bg-zinc-800 px-3 py-2">
    <div class="min-w-0">
      <label :for="id" class="block whitespace-nowrap text-sm font-semibold leading-5 text-zinc-300">
        {{ label }}
      </label>
      <span v-if="description" class="block whitespace-nowrap text-xs font-normal leading-4 text-zinc-500">{{ description }}</span>
    </div>

    <SwitchRoot
      :id
      v-model="model"
      :disabled
      class="relative ms-auto h-6 w-11 shrink-0 rounded-full border border-zinc-700 bg-zinc-950 outline-none transition-colors hover:border-zinc-500 focus-visible:border-lime-300 disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:border-lime-300 data-[state=checked]:bg-lime-300/20"
    >
      <SwitchThumb class="block h-4 w-4 translate-x-1 rounded-full bg-zinc-500 shadow-sm transition-transform data-[state=checked]:translate-x-5 data-[state=checked]:bg-lime-300" />
    </SwitchRoot>
  </div>
</template>
