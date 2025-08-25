<script setup lang="ts">
import { CatalogApi, ProvidersApi, type PlaylistRead, type ProviderRead, type TrackRead } from '@/api';
import AppContainer from '@/components/generic/AppContainer.vue';
import { get_authenticated_api_configuration } from '@/services/api';
import { decode_entity_id } from '@/utils/id';
import { useRouteParams } from '@vueuse/router';
import { computed, onBeforeMount, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { isAxiosError } from 'axios';
import PlaylistPageHeader from '@/components/library/PlaylistPageHeader.vue';
import AppLoaderScreen from '@/components/generic/AppLoaderScreen.vue';
import TrackResult from '@/components/library/TrackResult.vue';

const router = useRouter();

const isLoading = ref(true);
const playlistIdRaw = useRouteParams('id');
const playlistIdAndProvider = computed(() => {
  if (!playlistIdRaw.value) {
    return undefined;
  }

  const id = Array.isArray(playlistIdRaw.value) ? playlistIdRaw.value[0] : playlistIdRaw.value;
  return decode_entity_id(id);
});

const playlist = ref<PlaylistRead>();
const tracks = ref<TrackRead[]>();
const providers = ref<ProviderRead[]>([]);
const playlistsProvider = computed(() => {
  return providers.value.find(provider => provider.provider_name === playlist.value?.meta.provider_name);
});

const config = get_authenticated_api_configuration();
const catalogApi = new CatalogApi(config);
const providersApi = new ProvidersApi(config);

const fetchPlaylist = async () => {
  if (!playlistIdRaw.value || !playlistIdAndProvider.value) {
    return;
  }

  const { provider, provider_id } = playlistIdAndProvider.value;

  if (!provider || !provider_id) {
    return;
  }

  try {
    const response = await catalogApi.getPlaylist(provider_id, provider);
    playlist.value = response.data;
  } catch (e) {
    if (isAxiosError(e)) {
      switch (e.response?.status) {
        case 404:
          console.warn('Playlist not found:', e);
          router.push({ name: 'playlists' });
          break;
        default:
          console.error('An error occurred:', e);
      }
    } else {
      console.error('An unknown error occurred:', e);
    }
  }
};

const fetchPlaylistTracks = async () => {
  if (!playlist.value) {
    return;
  }

  const { provider, provider_id } = playlistIdAndProvider.value;

  if (!provider || !provider_id) {
    return;
  }

  try {
    const response = await catalogApi.getPlaylistTracks(provider_id, provider);
    tracks.value = response.data.items;
  } catch (e) {
    if (isAxiosError(e)) {
      switch (e.response?.status) {
        case 404:
          console.warn('Playlist not found:', e);
          router.push({ name: 'playlists' });
          break;
        default:
          console.error('An error occurred:', e);
      }
    } else {
      console.error('An unknown error occurred:', e);
    }
  }
}

const fetchProviders = async () => {
  try {
    const response = await providersApi.getValidProviderNames();
    providers.value = response.data.items ?? [];
  } catch (e) {
    console.error('An error occurred while fetching providers:', e);
  }
};

onBeforeMount(() => {
  if (!playlistIdRaw.value) {
    router.push({ name: 'playlists' });
  }
});

onMounted(async () => {
  isLoading.value = true;
  await fetchPlaylist();
  await fetchPlaylistTracks();
  await fetchProviders();
  isLoading.value = false;
});
</script>

<template>
  <AppContainer is="main">
    <AppLoaderScreen v-if="isLoading" />
    <template v-else>
      <PlaylistPageHeader :playlist :provider="playlistsProvider" />
      <div class="flex flex-col gap-3 my-8" v-if="tracks">
        <TrackResult :track :providers v-for="track in tracks" :key="track.identifiers.provider_id" />
      </div>
    </template>
  </AppContainer>
</template>
