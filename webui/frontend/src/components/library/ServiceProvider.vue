<script setup lang="ts">
import { type ProviderRead } from '@/api';
import AppCard from '../card/AppCard.vue';

defineProps<{
  provider: ProviderRead;
}>()
</script>

<template>
  <AppCard class="flex gap-4">
    <div class="flex items-center justify-center w-14 h-14 p-2 rounded-2xl bg-zinc-600/40 ring-1 ring-zinc-700">
      <img :src="provider.ui.favicon" :alt="`${provider.ui.display_name} logo`" width="40" height="40">
    </div>
    <div class="flex flex-col gap-1 flex-1">
      <h3 class="text-xl">{{ provider.ui.display_name }}</h3>
      <p class="text-zinc-400 font-normal">
        {{ provider.ui.description }}
      </p>
      <div v-if="$slots.form">
        <slot name="form" />
      </div>
    </div>
    <div v-if="$slots.linking" class="flex gap-3 ms-auto items-center">
      <slot name="linking" />
    </div>
  </AppCard>
</template>
