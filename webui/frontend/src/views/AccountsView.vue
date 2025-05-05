<script setup lang="ts">
import AppPageHeader from '@/components/generic/AppPageHeader.vue';
import AppContainer from '@/components/generic/AppContainer.vue';
import { type ProviderRead, ProvidersApi, YouTubeApi, DeezerApi, SubsonicApi, SpotifyApi } from '@/api';
import { get_authenticated_api_configuration } from '@/services/api';
import { onMounted, provide, ref } from 'vue';
import { isAxiosError } from 'axios';
import { useRouter } from 'vue-router';
import ServiceProvider from '@/components/library/ServiceProvider.vue';
import { Icon } from '@iconify/vue';
import SubsonicLoginForm from '@/components/service/SubsonicLoginForm.vue';
import DeezerARLForm from '@/components/service/DeezerARLForm.vue';
import AppButton from '@/components/button/AppButton.vue';

const providersApi = new ProvidersApi(get_authenticated_api_configuration());

const providers = ref<ProviderRead[]>([]);

const router = useRouter();

const loadProviders = async () => {
  try {
    const response = await providersApi.getValidProviderNames();

    if (response.data.items) {
      providers.value = response.data.items;
    } else {
      console.error('Backend returned an empty list of providers');
    }
  } catch (error) {
    if (isAxiosError(error)) {
      switch (error.response?.status) {
        case 401:
        case 403:
          router.push({ name: 'login' });
          break;
        default:
          console.error('Error loading providers:', error);
      }
    }
  }
};

onMounted(async () => {
  await loadProviders();
});

const unlinkProvider = async (provider: ProviderRead) => {
  try {
    switch (provider.provider_name) {
      case 'youtube':
        await new YouTubeApi(get_authenticated_api_configuration()).unlinkYouTubeAccount();
        break;
      case 'deezer':
        await new DeezerApi(get_authenticated_api_configuration()).unlinkDeezerAccount();
        break;
      case 'subsonic':
        await new SubsonicApi(get_authenticated_api_configuration()).unlinkSubsonicAccount();
        break;
      case 'spotify':
        await new SpotifyApi(get_authenticated_api_configuration()).unlinkSpotifyAccount();
        break;
      default:
        console.error('Unknown provider:', provider.provider_name);
    }

    await loadProviders();
  } catch (error) {
    if (isAxiosError(error)) {
      switch (error.response?.status) {
        case 401:
        case 403:
          router.push({ name: 'login' });
          break;
        default:
          console.error('Error unlinking provider:', error);
      }
    }
  }
};

const getOAuth2State = async (provider: ProviderRead) => {
  try {
    const response = await providersApi.generateProviderState(provider.provider_name, {
      redirect_uri: window.location.origin + window.location.pathname + window.location.search + '#' + provider.provider_name
    })

    return response.data.access_token;
  } catch (error) {
    if (isAxiosError(error)) {
      switch (error.response?.status) {
        case 401:
        case 403:
          router.push({ name: 'login' });
          break;
        default:
          console.error('Error getting OAuth2 state:', error);
      }
    }
  }
}

const goToOAuth2Page = async (provider: ProviderRead) => {
  const state = await getOAuth2State(provider);

  if (!state) {
    console.error('Invalid state');
    return;
  }

  const url = new URL(provider.linking.target_url);
  url.searchParams.set('state', state);

  window.location.href = url.toString();
}
</script>

<template>
  <AppContainer is="main">
    <AppPageHeader>
      <template #title>
        Manage Linked Accounts
      </template>
      <template #description>
        Manage your libraries by connecting them. Your credentials are stored encrypted.
      </template>
    </AppPageHeader>
    <div class="flex flex-col gap-4 mt-8">
      <template v-for="provider in providers" :key="provider.provider_name">
        <ServiceProvider :provider v-if="provider.linking.linked" :id="provider.provider_name">
          <template #linking>
            <AppButton type="button" tone="negative" @click="unlinkProvider(provider)">
              <Icon icon="material-symbols:link-off-rounded" class="inline-block text-2xl me-3" />UNLINK ACCOUNT
            </AppButton>
          </template>
        </ServiceProvider>
        <ServiceProvider :provider v-else :id="provider.provider_name">
          <template v-if="provider.linking.link_type === 'oauth2'" #linking>
            <AppButton type="button" @click="goToOAuth2Page(provider)">
              <Icon icon="material-symbols:add-link-rounded" class="inline-block text-2xl me-3" />LINK ACCOUNT
            </AppButton>
          </template>
          <template v-else-if="provider.linking.link_type === 'form'" #form>
            <SubsonicLoginForm :provider v-if="provider.provider_name === 'subsonic'" @linked="loadProviders" />
            <DeezerARLForm :provider v-else-if="provider.provider_name === 'deezer'" @linked="loadProviders" />
          </template>
        </ServiceProvider>
      </template>
    </div>
    <div class="text-sm text-zinc-700 py-5 flex flex-col gap-2 font-medium">
      <p>If you run into trouble, make sure you have properly configured all providers you wish to use.</p>
      <p>Services listed on this page are not affiliated with the tunesynctool project in any way. Tunesynctool cannot
        guarantee that the accounts you link won't get suspended or limited in any way. Use tunesynctool at your own
        risk.
      </p>
    </div>
  </AppContainer>
</template>
