<script setup lang="ts">
import type { PlaylistRead, ProviderRead } from '@/api';
import { Icon } from '@iconify/vue/dist/iconify.js';
import { onMounted, ref } from 'vue';

defineProps<{
  playlist?: PlaylistRead;
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
  <div class="flex items-center justify-center shrink-0 w-40 h-40 rounded-md bg-zinc-600/40 ring-1 ring-zinc-700 relative overflow-hidden">
    <img :src="provider?.ui.favicon" :alt="provider?.ui.display_name" class="absolute w-5 h-5 right-1 bottom-1" v-if="provider" />
    <template v-if="playlist?.assets.cover_image">
      <Icon icon="material-symbols-light:sentiment-sad-rounded" class="w-14 h-14 text-zinc-500 block" v-if="loadingError" />
      <img :src="playlist?.assets.cover_image" class="w-full h-full object-cover aspect-square" ref="coverImage" v-else />
    </template>
    <Icon icon="material-symbols:library-music-rounded" class="w-18 h-18 text-zinc-500 block" :class="{ 'animate-pulse': isLoading }" v-else />
  </div>
</template>
