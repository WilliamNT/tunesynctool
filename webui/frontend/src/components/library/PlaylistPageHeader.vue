<script setup lang="ts">
import type { PlaylistRead, ProviderRead } from '@/api';
import PlaylistCover from '../image/PlaylistCover.vue';
import { computed } from 'vue';

const props = defineProps<{
  playlist?: PlaylistRead;
  provider?: ProviderRead;
}>();

const shareUrl = computed(() => props.playlist?.meta.share_url ?? undefined)
const transferArguments = computed(() => {
  return {
    task: 'transfer',
    from_provider: props.playlist?.meta.provider_name,
    from_playlist: props.playlist?.identifiers.provider_id
  }
});
</script>

<template>
  <header class="flex gap-8 mt-6">
    <PlaylistCover :playlist :provider />
    <div class="flex flex-col gap-3 items-start justify-center">
      <h1 class="text-4xl text-white">
        {{ playlist?.title ?? 'n/a' }}
      </h1>
      <div class="text-md font-normal text-gray-400" v-if="playlist?.description">
        <div v-html="playlist.description"></div>
      </div>
      <div class="flex gap-4">
        <a :href="shareUrl" class="px-7 py-2 mt-3 text-black font-bold rounded-2xl transition-colors block text-center border-1" target="_blank" :class="{
          'opacity-45 cursor-not-allowed': !shareUrl,
          'bg-lime-400 border-lime-400 hover:bg-lime-500 hover:border-lime-500': !!shareUrl,
        }">
          Open On {{ provider?.ui.display_name ?? 'provider' }}
        </a>
        <RouterLink :to="{ name: 'tasks', query: transferArguments }" class="px-7 py-2 mt-3 rounded-2xl transition-colors block text-center border-1 text-black border-white bg-white hover:bg-slate-200 hover:border-slate-200" :class="{
          'opacity-45 cursor-not-allowed': !playlist
        }">
          Transfer
        </RouterLink>
      </div>
    </div>
  </header>
</template>
