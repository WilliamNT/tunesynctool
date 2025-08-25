import { Configuration } from '@/api';
import { useLocalStorage } from '@vueuse/core';
import { computed } from 'vue';

const ACCESS_TOKEN_KEY = 'access_token';

export const accessToken = useLocalStorage<string | undefined>(ACCESS_TOKEN_KEY, undefined);
export const isAuthenticated = computed(() => !!accessToken.value);

export function get_access_token(): string | undefined {
    return accessToken.value;
}

export function set_access_token(access_token: string): void {
    accessToken.value = access_token;
}

export function delete_access_token(): void {
    accessToken.value = undefined;
}

export function is_access_token_set(): boolean {
    return !!get_access_token();
}

export function get_api_configuration(access_token?: string): Configuration {
    return new Configuration({
        basePath: import.meta.env.VITE_API_BASE_URL,
        accessToken: access_token,
    });
}

export function get_authenticated_api_configuration(): Configuration {
    const access_token = get_access_token();
    if (!access_token) {
        throw new Error('Access token is not set');
    }

    return get_api_configuration(access_token);
}
