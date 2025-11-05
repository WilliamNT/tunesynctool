<script setup lang="ts">
import { LibraryApi, TaskKind, TasksApi, type PlaylistRead, type ProviderRead } from '@/api';
import AppButton from '../button/AppButton.vue';
import AppFormSpacer from '../form/AppFormSpacer.vue';
import { computed, onMounted, ref, watch } from 'vue';
import { Icon } from '@iconify/vue';
import ProviderSelector from '@/components/service/ProviderSelector.vue'
import { get_access_token, get_api_configuration } from '@/services/api';
import PlaylistSelector from './PlaylistSelector.vue';
import { useRouteQuery } from '@vueuse/router';
import { isAxiosError } from 'axios';

const props = defineProps<{
  providers: ProviderRead[];
}>();

const providers = computed(() => props.providers.filter((provider) => provider.is_configured && provider.linking.linked));
const config = get_api_configuration(get_access_token());
const libraryApi = new LibraryApi(config);
const tasksApi = new TasksApi(config);
const isLoading = ref(false);
const playlists = ref<PlaylistRead[]>([]);

const disallowSubmit = computed(() => {
  return !sourceProviderChoice.value || !targetProviderChoice.value || !selectedPlaylist.value;
});

const sourceProviderName = useRouteQuery<string>('from_provider');
const sourceProviderChoice = computed(() => {
  return providers.value.find((provider) => provider.provider_name === sourceProviderName.value);
});

const targetProviderName = useRouteQuery<string>('to_provider');
const targetProviderChoice = computed(() => {
  return providers.value.find((provider) => provider.provider_name === targetProviderName.value);
});

const fetchLibraryPlaylists = async () => {
  try {
    const response = await libraryApi.getLibraryPlaylists();

    if (response.data.items) {
      playlists.value = response.data.items;
    }
  } catch (error) {
    if (isAxiosError(error)) {
      console.error(`Failed to fetch available playlists. Error: "${error.response?.data ?? error.message}""`)
    }
  }
}

const transferablePlaylists = ref<PlaylistRead[]>([]);
const filterOnlyPlaylistsFromSourceProvider = async () => {
  const provider_name = sourceProviderChoice.value?.provider_name;

  if (!provider_name) {
    return;
  }

  transferablePlaylists.value = playlists.value.filter((p) => p.meta.provider_name === provider_name);
};

const selectedPlaylistId = useRouteQuery<string | undefined>('from_playlist');
const selectedPlaylist = computed(() => {
  return transferablePlaylists.value.find((playlist) => playlist.identifiers.provider_id === selectedPlaylistId.value);
});

watch(providers, (newProviders) => {
  if (!sourceProviderName.value && newProviders.length > 0) {
    sourceProviderName.value = newProviders[0].provider_name;
  }

  if (!targetProviderName.value && newProviders.length > 0) {
    targetProviderName.value = newProviders[0].provider_name;
  }
}, {
  immediate: true
});

watch([sourceProviderChoice, playlists], filterOnlyPlaylistsFromSourceProvider, {
  immediate: true
});

watch(sourceProviderChoice, (newValue, oldValue) => {
  if (newValue !== oldValue && selectedPlaylist.value?.meta.provider_name !== newValue) {
    selectedPlaylistId.value = undefined;
  }
})

onMounted(fetchLibraryPlaylists);

const onSubmit = async () => {
  if (!sourceProviderChoice.value || !targetProviderChoice.value || !selectedPlaylist.value) {
    return;
  }

  isLoading.value = true;

  await tasksApi.transferPlaylist({
    from_provider: sourceProviderChoice.value.provider_name,
    to_provider: targetProviderChoice.value.provider_name,
    from_playlist: selectedPlaylist.value?.identifiers.provider_id,
    kind: TaskKind.PlaylistTransfer, // hardcoded for now, but will need to be dynamic later
  })

  selectedPlaylistId.value = undefined;

  isLoading.value = false;
}
</script>

<template>
  <form @submit.prevent="onSubmit">
    <AppFormSpacer direction="row" class="items-start">
      <PlaylistSelector :playlists="transferablePlaylists" :disabled="isLoading" v-model="selectedPlaylistId" :is-loading />
      <div class="flex gap-2">
        <ProviderSelector :providers v-model="sourceProviderName" />
        <Icon icon="material-symbols-light:arrow-right-alt-rounded" class="block text-3xl h-full my-auto text-zinc-400" />
        <ProviderSelector :providers v-model="targetProviderName" />
      </div>
      <AppButton type="submit" :disabled="disallowSubmit || isLoading" class="min-w-30">
        <Icon icon="svg-spinners:3-dots-bounce" class="inline-block text-2xl" v-if="isLoading"/>
        <template v-else>
          Transfer
        </template>
      </AppButton>
    </AppFormSpacer>
  </form>
</template>
