<script setup lang="ts">
import { CatalogApi, type ProviderRead } from '@/api';
import * as zod from 'zod';
import { useForm } from 'vee-validate';
import { toTypedSchema } from '@vee-validate/zod';
import { get_authenticated_api_configuration } from '@/services/api';
import AppButton from '../button/AppButton.vue';
import AppField from '../form/AppField.vue';
import AppFormSpacer from '../form/AppFormSpacer.vue';
import { isAxiosError } from 'axios';
import router from '@/router';
import { computed, onMounted, ref, toRefs, watch } from 'vue';
import { Icon } from '@iconify/vue';
import { ComboboxAnchor, ComboboxContent, ComboboxItem, ComboboxRoot, ComboboxTrigger, ComboboxViewport } from 'reka-ui';

const props = defineProps<{
  providers: ProviderRead[];
}>();

const providers = computed(() => props.providers.filter((provider) => provider.is_configured && provider.linking.linked));

const catalogApi = new CatalogApi(get_authenticated_api_configuration());

const schema = zod.object({
  searchQuery: zod.string().min(3, 'Search query is required').max(100, 'Search query must be less than 100 characters')
});

const { defineField, handleSubmit, errors, isFieldValid } = useForm({
  initialValues: {
    searchQuery: ''
  },
  validationSchema: toTypedSchema(schema),
});

const [searchQuery, searchQueryAttributes] = defineField('searchQuery');

const emit = defineEmits(['result']);

const isSearching = ref(false);
const onSubmit = handleSubmit(async (values) => {
  const { searchQuery } = values;

  try {
    if (!providerChoice.value) {
      return;
    }

    isSearching.value = true;
    const results = await catalogApi.searchTracks(providerChoice.value.provider_name, searchQuery, 10);

    if (results) {
      emit('result', results.data);
    }

    isSearching.value = false;
  } catch (error) {
    if (isAxiosError(error)) {
      switch (error.response?.status) {
        case 401:
        case 403:
          router.push({ name: 'login' });
          break;
        default:
          console.error('Error while fetching search results:', error);
      }
    }
  }
});

const disallowSearch = computed(() => {
  return !isFieldValid('searchQuery') || !providerChoice.value;
});

const providerName = ref<string>();
const providerChoice = computed(() => {
  return providers.value.find((provider) => provider.provider_name === providerName.value);
});

watch(providers, (newProviders) => {
  if (!providerName.value && newProviders.length > 0) {
    providerName.value = newProviders[0].provider_name;
  }
}, {
  immediate: true
});
</script>

<template>
  <form @submit.prevent="onSubmit">
    <AppFormSpacer direction="row" class="items-start">
      <AppField type="search" name="searchQuery" placeholder="Enter track title or artist name..." v-model="searchQuery" :error="errors.searchQuery" v-bind="searchQueryAttributes" :disabled="isSearching" />
      <ComboboxRoot v-model="providerName" class="relative block shrink-0" :disabled="isSearching">
      <ComboboxAnchor class="bg-zinc-800 px-3 py-2 rounded-xl border outline-none transition-colors data-[placeholder]:text-zinc-300/30 flex items-center gap-2" :class="{
        'border-red-400': providers.length === 0,
        'border-zinc-700': providers.length > 0,
      }">
        <ComboboxTrigger class="disabled:opacity-50" v-if="providers.length > 0">
          <div class="flex gap-2 items-center min-w-0">
            <img :src="providerChoice.ui.favicon" alt="" v-if="providerChoice?.ui.favicon" class="h-5 object-cover" />
            <span class="whitespace-nowrap text-zinc-300">{{ providerChoice?.ui.display_name ?? 'Please choose' }}</span>
            <Icon icon="radix-icons:chevron-down" class="h-4 w-4 text-zinc-400 shrink-0" />
          </div>
        </ComboboxTrigger>
        <ComboboxTrigger class="disabled:opacity-50" v-else>
          <div class="flex gap-2 items-center min-w-0 text-red-400">
            <Icon icon="material-symbols:error-outline-rounded" class="inline-block text-2xl" />
            <span class="whitespace-nowrap ">No providers are linked or configured!</span>
          </div>
        </ComboboxTrigger>
      </ComboboxAnchor>

        <ComboboxContent class="bg-zinc-800 border-1 border-zinc-700 rounded-xl shadow-lg overflow-hidden absolute z-10 w-full mt-2 min-w-[200px]" v-if="providers.length > 0">
          <ComboboxViewport class="p-[5px]">
            <ComboboxItem v-for="provider in providers" :key="provider.provider_name" :value="provider.provider_name">
                <div class="flex gap-2 items-center hover:bg-zinc-700/50 cursor-pointer transition-all rounded-lg p-2">
                  <img :src="provider.ui.favicon" alt="" v-if="provider?.ui.favicon" class="h-5 object-cover" />
                  <span class="truncate text-md text-zinc-300/90">
                    {{ provider.ui.display_name }}
                  </span>
                </div>
              </ComboboxItem>
          </ComboboxViewport>
        </ComboboxContent>
      </ComboboxRoot>
      <AppButton type="submit" :disabled="disallowSearch || isSearching" class="min-w-30">
        <Icon icon="svg-spinners:3-dots-bounce" class="inline-block text-2xl" v-if="isSearching"/>
        <template v-else>
          Search
        </template>
      </AppButton>
    </AppFormSpacer>
  </form>
</template>
