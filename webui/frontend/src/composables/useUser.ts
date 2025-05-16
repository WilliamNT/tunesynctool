import { UsersApi, type UserRead } from '@/api';
import { get_authenticated_api_configuration } from '@/services/api';
import { isAxiosError } from 'axios';
import { useRouter } from 'vue-router';

export const useUser = async (): Promise<UserRead | null> => {
    const config = get_authenticated_api_configuration();
    const usersApi = new UsersApi(config);

    const router = useRouter();

    try {
        const response = await usersApi.getAuthenticatedUser();

        if (response.data) {
            return response.data;
        } else {
            console.error('Backend returned an empty user');
        }
    } catch (error) {
        if (isAxiosError(error)) {
            switch (error.response?.status) {
                case 401:
                case 403:
                    router.push({ name: 'login' });
                    break;
                default:
                    console.error('Error loading user:', error);
            }
        }
    }

    return null;
};
