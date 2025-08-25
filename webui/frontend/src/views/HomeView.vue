<script setup lang="ts">
import { LibraryApi, type PlaylistRead, type ProviderRead, type UserRead } from '@/api';
import AppContainer from '@/components/generic/AppContainer.vue';
import AppPageHeader from '@/components/generic/AppPageHeader.vue';
import PlaylistCard from '@/components/library/PlaylistCard.vue';
import { useProviders } from '@/composables/useProviders';
import { get_authenticated_api_configuration } from '@/services/api';
import { computed, onMounted, ref } from 'vue';
import { useUser } from '@/composables/useUser';
import AppLoaderScreen from '@/components/generic/AppLoaderScreen.vue';
import { Icon } from '@iconify/vue';

const providers = ref<ProviderRead[]>([]);
const playlists = ref<PlaylistRead[]>([]);
const user = ref<UserRead | null>(null);
const isLoading = ref(false);

const loadPlaylists = async () => {
  const libraryApi = new LibraryApi(get_authenticated_api_configuration());
  const results = await libraryApi.getLibraryPlaylists();

  playlists.value = results.data.items ?? [];
};

onMounted(async () => {
  isLoading.value = true;

  providers.value = await useProviders();
  await loadPlaylists();
  user.value = await useUser();

  isLoading.value = false;
});

const areAnyProvidersLinked = computed(() => {
  return providers.value.filter(p => p.linking.linked).length > 0
});

const getPlaylistKey = (playlist: PlaylistRead) => {
  return `${playlist.meta.provider_name}-${playlist.identifiers.provider_id}`;
};

const providersWithPlaylists = computed(() => {
  return providers.value.filter((provider) => {
    return playlists.value.some((playlist) => playlist.meta.provider_name === provider.provider_name);
  });
});
</script>

<template>
  <AppContainer is="main">
    <AppLoaderScreen v-if="isLoading" />
    <template v-else>
      <AppPageHeader>
        <template #title>
          Welcome {{ user?.username ?? 'guest' }}!
        </template>
        <template #description>
          Here are your playlists from all linked services.
        </template>
      </AppPageHeader>
      <template v-if="providersWithPlaylists.length > 0">
        <div class="flex flex-col gap-4 items-center mt-10" v-for="provider in providersWithPlaylists" :key="provider.provider_name">
          <div class="flex items-center gap-3 w-full mb-3">
            <img :src="provider.ui.favicon" alt="" class="w-6 h-6" />
            <h2 class="text-2xl">{{ provider.ui.display_name }}</h2>
            <hr class="flex-1 border-zinc-700 border-0.5 ms-5" />
          </div>
          <div class="flex gap-4 flex-wrap">
            <template v-for="playlist in playlists" :key="getPlaylistKey(playlist)">
              <PlaylistCard :providers :playlist v-if="provider.provider_name === playlist.meta.provider_name" />
            </template>
          </div>
        </div>
      </template>
      <div class="flex items-center justify-center h-full" v-else>
        <div class="flex flex-col items-center gap-4">
          <Icon icon="material-symbols-light:library-music-rounded" class="text-gray-400 text-7xl"/>
          <p class="text-md font-normal text-gray-400">{{ areAnyProvidersLinked ? 'Your library is empty.' : 'Please configure at least one provider to access your library.' }}</p>
        </div>
      </div>
    </template>
  </AppContainer>
</template>
