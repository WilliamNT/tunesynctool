<script setup lang="ts">
import type { PlaylistRead, ProviderRead, TrackRead } from '@/api';
import { Icon } from '@iconify/vue/dist/iconify.js';
import { computed, onMounted, ref } from 'vue';

const props = defineProps<{
  playlist?: PlaylistRead | null;
  track?: TrackRead | null;
  provider?: ProviderRead;
}>();

const coverImage = ref<HTMLImageElement | null>(null);
const loadingError = ref(false);
const isLoading = ref(true);

const onCoverImageError = () => {
  if (coverImage.value) {
    coverImage.value.classList.add('opacity-0');
    loadingError.value = true;
    isLoading.value = false;
  }
};

onMounted(() => {
  if (coverImage.value) {
    coverImage.value.addEventListener('error', onCoverImageError);
    coverImage.value.addEventListener('load', () => {
      isLoading.value = false;
    });
  }
});

const trackUrl = computed(() => props.track?.meta.share_url ? props.track.meta.share_url : '#');
</script>

<template>
  <div class="w-16 h-16 bg-zinc-600/40 ring-1 ring-zinc-700 relative rounded-md">
    <a :href="trackUrl" v-if="track">
      <img :src="track.assets.cover_image" :alt="`Current item: ${track?.title} by ${track?.author.primary}`" class="absolute w-8 h-8 -right-1 -bottom-1 rounded-sm ring-1 shadow-xl ring-zinc-700" v-if="track.assets.cover_image" />
      <Icon icon="material-symbols:music-note-rounded" class="absolute text-3xl p-0.5 -right-1 -bottom-1 text-zinc-500 rounded-md bg-zinc-800 ring-1 ring-zinc-700 shadow-xl" v-else />
    </a>
    <div class="flex items-center justify-center w-full h-full">
      <template v-if="playlist?.assets.cover_image">
        <Icon icon="material-symbols-light:sentiment-sad-rounded" class="w-14 h-14 text-zinc-500 block" v-if="loadingError" />
        <img :src="playlist?.assets.cover_image" class="w-full h-full object-cover aspect-square rounded-md" ref="coverImage" v-else />
      </template>
      <Icon icon="material-symbols-light:library-music-rounded" class="w-14 h-14 text-zinc-500 block rounded-md" :class="{ 'animate-pulse': isLoading }" v-else />
    </div>
  </div>
</template>
