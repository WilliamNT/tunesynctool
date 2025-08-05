<script setup lang="ts">
import type { PlaylistRead } from '@/api';
import { ComboboxAnchor, ComboboxContent, ComboboxItem, ComboboxRoot, ComboboxTrigger, ComboboxViewport } from 'reka-ui';
import { Icon } from '@iconify/vue';
import { computed } from 'vue';

const props = withDefaults(defineProps<{
  playlists?: PlaylistRead[];
  disabled?: boolean;
  isLoading?: boolean;
}>(), {
  disabled: false,
  playlists: () => [],
  isLoading: false,
});

const modelValue = defineModel<string>();
const selectedPlaylist = computed(() => {
  return props.playlists.find((p) => p.identifiers.provider_id === modelValue.value);
});
</script>

<template>
  <ComboboxRoot v-model="modelValue" class="relative block shrink-0 flex-1" :disabled>
    <ComboboxAnchor class="bg-zinc-800 px-3 py-2 rounded-xl border outline-none transition-colors data-[placeholder]:text-zinc-300/30 flex items-center gap-2 border-zinc-700">
      <ComboboxTrigger class="disabled:opacity-50 w-full" v-if="isLoading">
        <div class="flex gap-2 items-center min-w-0">
          <span class="whitespace-nowrap text-zinc-300 animate-pulse">Loading playlists...</span>
          <Icon icon="radix-icons:chevron-down" class="h-4 w-4 text-zinc-400 shrink-0 ms-auto" />
        </div>
      </ComboboxTrigger>
      <ComboboxTrigger class="disabled:opacity-50 w-full" v-else-if="playlists.length > 0">
        <div class="flex gap-2 items-center min-w-0">
          <img :src="selectedPlaylist?.assets.cover_image" alt="" v-if="selectedPlaylist?.assets.cover_image" class="h-5 object-cover rounded-sm" />
          <span class="whitespace-nowrap text-zinc-300">{{ selectedPlaylist?.title ?? 'Please choose' }}</span>
          <Icon icon="radix-icons:chevron-down" class="h-4 w-4 text-zinc-400 shrink-0 ms-auto" />
        </div>
      </ComboboxTrigger>
      <ComboboxTrigger class="disabled:opacity-50" v-else>
        <div class="flex gap-2 items-center min-w-0">
          <Icon icon="material-symbols-light:sentiment-sad-rounded" class="inline-block text-2xl ms-auto" />
          <span class="whitespace-nowrap ">You don't have any playlists</span>
        </div>
      </ComboboxTrigger>
    </ComboboxAnchor>

    <ComboboxContent class="bg-zinc-800 border-1 border-zinc-700 rounded-xl shadow-lg overflow-hidden absolute z-10 w-full mt-2 min-w-[200px] max-h-56" v-if="playlists.length > 0">
      <ComboboxViewport class="p-[5px]">
        <ComboboxItem v-for="playlist in playlists" :key="playlist.identifiers.provider_id" :value="playlist.identifiers.provider_id">
          <div class="flex gap-3 items-center hover:bg-zinc-700/50 cursor-pointer transition-all rounded-lg py-1 px-2">
            <img :src="playlist.assets.cover_image" alt="" v-if="playlist.assets.cover_image" class="h-8 object-cover rounded-sm" />
            <div class="flex flex-col">
              <span class="truncate text-md text-zinc-300/90">{{ playlist.title }}</span>
              <span class="truncate text-sm text-zinc-500">By {{ playlist.author.primary ?? 'an unknown user' }}</span>
            </div>
          </div>
        </ComboboxItem>
      </ComboboxViewport>
    </ComboboxContent>
  </ComboboxRoot>
</template>
