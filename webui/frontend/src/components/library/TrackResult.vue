<script setup lang="ts">
import type { TrackRead, ProviderRead } from '@/api';
import { computed } from 'vue';
import AppCard from '../card/AppCard.vue';
import { Icon } from '@iconify/vue/dist/iconify.js';
import { formatDuration, intervalToDuration } from 'date-fns';

const props = defineProps<{
  track: TrackRead;
  providers: ProviderRead[];
}>();

const provider = computed(() => props.providers.find((p) => p.provider_name === props.track.meta.provider_name));
const artists = computed(() => {
  const artists = props.track.author.collaborating ?? [];

  if (props.track.author.primary) {
    artists.unshift(props.track.author.primary);
  }

  return artists.join(', ');
});

const duration = computed(() => {
  if (!props.track.duration) {
    return 'n/a';
  }

  const x = intervalToDuration({
    start: 0,
    end: props.track.duration * 1000,
  });

  return formatDuration(x, {
    delimiter: ', ',
    format: ['hours', 'minutes', 'seconds'],
  })
});
</script>

<template>
  <a :href="track.meta.share_url ?? `#${track.meta.provider_name}-${track.identifiers.provider_id}`" :target="track.meta.share_url ? '_blank' : undefined">
    <AppCard class="rounded-2xl flex gap-4 relative overflow-hidden">
      <div class="flex items-center justify-center w-16 h-16 rounded-md bg-zinc-600/40 ring-1 ring-zinc-700 relative overflow-hidden">
        <img :src="provider?.ui.favicon" :alt="provider?.ui.display_name" class="absolute w-5 h-5 right-0.5 bottom-0.5" v-if="provider" />
        <img :src="track.assets.cover_image" class="w-full h-full object-cover aspect-square" v-if="track.assets.cover_image" />
        <Icon icon="material-symbols:music-note-rounded" class="w-14 h-14 text-zinc-500 block" v-else />
      </div>
      <div class="flex flex-col gap-0.5">
        <h3 class="truncate font-black text-white text-lg m-0 p-0">{{ track.title ?? 'n/a' }}</h3>
        <ul class="flex gap-2 list-none p-0 m-0 text-sm font-medium text-zinc-400">
          <li class="relative pl-3.5 first:pl-0 before:content-['•'] before:absolute before:left-0 first:before:content-[''] before:text-zinc-500 truncate">
            {{ artists }}
          </li>
          <li class="relative pl-3.5 first:pl-0 before:content-['•'] before:absolute before:left-0 first:before:content-[''] before:text-zinc-500 truncate" v-if="track.album_name">
            {{ track.album_name }}
          </li>
          <li class="relative pl-3.5 first:pl-0 before:content-['•'] before:absolute before:left-0 first:before:content-[''] before:text-zinc-500 truncate" v-if="track.track_number">
            # {{ track.track_number }}
          </li>
          <li class="relative pl-3.5 first:pl-0 before:content-['•'] before:absolute before:left-0 first:before:content-[''] before:text-zinc-500 truncate" v-if="track.release_year">
            {{ track.release_year }}
          </li>
          <li class="relative pl-3.5 first:pl-0 before:content-['•'] before:absolute before:left-0 first:before:content-[''] before:text-zinc-500 truncate" v-if="track.duration">
            {{ duration }}
          </li>
        </ul>
      </div>
      <div class="absolute blur-3xl w-full brightness-150 left-0 top-0  pointer-events-none">
        <img :src="track.assets.cover_image" alt="" v-if="track.assets.cover_image" class="object-cover w-full h-full opacity-10 block -bottom-1/2" />
        <div class="bg-white h-full w-1/2 opacity-10" v-else></div>
      </div>
    </AppCard>
  </a>
</template>
