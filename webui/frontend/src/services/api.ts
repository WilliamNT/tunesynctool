import { Configuration } from '@/api';

export function get_access_token(): string | undefined {
    return localStorage.getItem('access_token') ?? undefined;
}

export function set_access_token(access_token: string): void {
    localStorage.setItem('access_token', access_token);
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
