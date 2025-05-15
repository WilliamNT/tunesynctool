<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';
import AppContainer from '@/components/generic/AppContainer.vue';
import AppPageHeader from '@/components/generic/AppPageHeader.vue';
import AppCard from '@/components/card/AppCard.vue';
import { type ProviderRead, type SearchResultCollectionTrackRead, type TrackRead } from '@/api';
import { useProviders } from '@/composables/useProviders';
import SimpleSearchForm from '@/components/service/SimpleSearchForm.vue';
import TrackResult from '@/components/library/TrackResult.vue';

const loading = ref(false);

const providers = ref<ProviderRead[]>([]);
const results = ref<SearchResultCollectionTrackRead>();

onMounted(async () => {
  loading.value = true;
  providers.value = await useProviders();
  loading.value = false;
});
</script>

<template>
  <AppContainer is="main">
    <AppPageHeader>
      <template #title>
        Search tracks
      </template>
      <template #description>
        Search for any track available on your linked services. Please note that this feature only supports retrieving tracks, not albums or playlists.
      </template>
    </AppPageHeader>
    <div class="flex flex-col mt-8">
      <AppCard>
        <SimpleSearchForm :providers="providers" @result="(r) => results = r" />
      </AppCard>
      <div class="flex flex-col gap-3" v-if="results">
        <p class="text-xl font-black mt-5 mb-2">{{ results?.item_count ?? 0 }} results for "{{ results?.query }}"</p>
        <TrackResult :track :providers="providers" v-for="track in results.items" :key="track.identifiers.provider_id" />
      </div>
    </div>
  </AppContainer>
</template>
