<script setup lang="ts">
import { LibraryApi, type PlaylistRead, type ProviderRead } from '@/api';
import AppContainer from '@/components/generic/AppContainer.vue';
import AppPageHeader from '@/components/generic/AppPageHeader.vue';
import PlaylistCard from '@/components/library/PlaylistCard.vue';
import { useProviders } from '@/composables/useProviders';
import { get_authenticated_api_configuration } from '@/services/api';
import { computed, onMounted, ref } from 'vue';

const providers = ref<ProviderRead[]>([]);
const playlists = ref<PlaylistRead[]>([]);

const loadPlaylists = async () => {
  const libraryApi = new LibraryApi(get_authenticated_api_configuration());
  const results = await libraryApi.getLibraryPlaylists();

  playlists.value = results.data.items ?? [];
}

onMounted(async () => {
  providers.value = await useProviders();
  await loadPlaylists();
});

const getPlaylistKey = (playlist: PlaylistRead) => {
  return `${playlist.meta.provider_name}-${playlist.identifiers.provider_id}`;
}


const providersWithPlaylists = computed(() => {
  return providers.value.filter((provider) => {
    return playlists.value.some((playlist) => playlist.meta.provider_name === provider.provider_name);
  });
});
</script>

<template>
  <AppContainer is="main">
    <AppPageHeader>
      <template #title>
        My Library
      </template>
    </AppPageHeader>
    <div class="flex flex-col gap-4 mt-8" v-for="provider in providersWithPlaylists" :key="provider.provider_name">
        <div class="flex items-center gap-3">
          <img :src="provider.ui.favicon" alt="" class="w-6 h-6" />
          <h2 class="font-black text-2xl">{{ provider.ui.display_name }}</h2>
        </div>
        <div class="flex gap-4 flex-wrap">
          <template v-for="playlist in playlists" :key="getPlaylistKey(playlist)">
            <PlaylistCard :providers :playlist v-if="provider.provider_name === playlist.meta.provider_name" />
          </template>
        </div>
    </div>
  </AppContainer>
</template>
