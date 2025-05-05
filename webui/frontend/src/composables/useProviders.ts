import { ProvidersApi, type ProviderRead } from "@/api";
import { get_authenticated_api_configuration } from "@/services/api";
import { isAxiosError } from "axios";
import { ref } from "vue";
import { useRouter } from "vue-router";

export const useProviders = async (): Promise<ProviderRead[]> => {
  const config = get_authenticated_api_configuration();
  const providersApi = new ProvidersApi(config);

  const router = useRouter();

  try {
    const response = await providersApi.getValidProviderNames();

    if (response.data.items) {
      return response.data.items ?? [];
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

  return [];
};
