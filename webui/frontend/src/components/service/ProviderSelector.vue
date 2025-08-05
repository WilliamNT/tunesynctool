<script setup lang="ts">
import type { ProviderRead } from '@/api';
import { computed, useAttrs, watch } from 'vue';
import { ComboboxAnchor, ComboboxContent, ComboboxItem, ComboboxRoot, ComboboxTrigger, ComboboxViewport } from 'reka-ui';
import { Icon } from '@iconify/vue';

const props = withDefaults(defineProps<{
  providers: ProviderRead[];
  disabled?: boolean;
}>(), {
  disabled: false,
});

const providers = computed(() => props.providers.filter((provider) => provider.is_configured && provider.linking.linked));

const providerName = defineModel<string>();
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

const emit = defineEmits(['update:modelValue', 'blur']);
</script>

<template>
  <ComboboxRoot v-model="providerName" class="relative block shrink-0" :disabled>
    <ComboboxAnchor
      class="bg-zinc-800 px-3 py-2 rounded-xl border outline-none transition-colors data-[placeholder]:text-zinc-300/30 flex items-center gap-2"
      :class="{
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
</template>
