<script setup lang="ts">
import type { ProviderRead, TrackRead } from '@/api';
import { Icon } from '@iconify/vue/dist/iconify.js';
import { onMounted, ref } from 'vue';

defineProps<{
  track: TrackRead;
  provider?: ProviderRead;
}>();

const coverImage = ref<HTMLImageElement | null>(null);
const loadingError = ref(false);
const isLoading = ref(false);

const onCoverImageError = () => {
  if (coverImage.value) {
    coverImage.value.classList.add('opacity-0');
    loadingError.value = true;
    isLoading.value = false;
  }
};

onMounted(() => {
  if (coverImage.value) {
    isLoading.value = true;
    coverImage.value.addEventListener('error', onCoverImageError);
    coverImage.value.addEventListener('load', () => {
      isLoading.value = false;
    });
  }
});
</script>

<template>
  <div
    class="flex items-center justify-center w-16 h-16 rounded-md bg-zinc-600/40 ring-1 ring-zinc-700 relative overflow-hidden">
    <img :src="provider?.ui.favicon" :alt="provider?.ui.display_name" class="absolute w-5 h-5 right-0.5 bottom-0.5" v-if="provider" />
    <template v-if="track.assets.cover_image">
      <Icon icon="material-symbols-light:sentiment-sad-rounded" class="w-14 h-14 text-zinc-500 block" v-if="loadingError" />
      <img :src="track.assets.cover_image" class="w-full h-full object-cover aspect-square" ref="coverImage" v-else />
    </template>
    <Icon icon="material-symbols:music-note-rounded" class="w-14 h-14 text-zinc-500 block" :class="{ 'animate-pulse': isLoading }" v-else />
  </div>
</template>
