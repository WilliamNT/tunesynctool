<script setup lang="ts">
import type { PlaylistRead, ProviderRead } from '@/api';
import AppCard from '../card/AppCard.vue';
import { computed } from 'vue';
import { Icon } from '@iconify/vue';

const props = defineProps<{
  playlist: PlaylistRead;
  providers: ProviderRead[];
}>();

const provider = computed(() => props.providers.find((p) => p.provider_name === props.playlist.meta.provider_name));
</script>

<template>
  <AppCard class="overflow-hidden relative">
    <div class="flex flex-col gap-2 max-w-40">
      <div class="flex items-center justify-center w-40 h-40 rounded-md bg-zinc-600/40 ring-1 ring-zinc-700 relative overflow-hidden">
        <img :src="provider?.ui.favicon" :alt="provider?.ui.display_name" class="absolute w-6 h-6 right-1 bottom-1" v-if="provider" />
        <img :src="playlist.assets.cover_image" :alt="`Cover image for ${playlist.title}`" v-if="playlist.assets.cover_image" class="w-full h-full object-cover">
        <Icon icon="material-symbols:library-music-rounded" class="w-14 h-14 text-zinc-500 block" v-else />
      </div>
      <div>
        <h6 class="font-black truncate h-full text-normal text-white">{{ playlist.title ?? 'n/a' }}</h6>
        <p class="text-sm font-semibold text-zinc-400/85 truncate">by {{ playlist.author.primary ?? 'n/a' }}</p>
      </div>
      <img :src="playlist.assets.cover_image" :alt="`Cover image for ${playlist.title}`" v-if="playlist.assets.cover_image" class="blur-3xl absolute object-cover -bottom-1/2 opacity-30 w-50 h-50 brightness-150">
    </div>
  </AppCard>
</template>
