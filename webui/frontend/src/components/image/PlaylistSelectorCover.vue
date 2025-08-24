<script setup lang="ts">
import type { PlaylistRead } from '@/api';
import { Icon } from '@iconify/vue/dist/iconify.js';
import { onMounted, ref } from 'vue';

defineProps<{
  playlist?: PlaylistRead;
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
  <div class="flex items-center justify-center w-8 h-8 rounded-sm bg-zinc-600/40 ring-1 ring-zinc-700 relative overflow-hidden">
    <Icon icon="material-symbols:library-music-rounded" class="w-6 h-6 text-zinc-500 block" :class="{ 'animate-pulse': isLoading }" v-if="isLoading || !playlist?.assets.cover_image" />
    <template v-else>
      <Icon icon="material-symbols-light:sentiment-sad-rounded" class="w-6 h-6 text-zinc-500 block" v-if="loadingError" />
      <img :src="playlist.assets.cover_image" class="w-full h-full object-cover aspect-square" ref="coverImage" v-else />
    </template>
  </div>
</template>
