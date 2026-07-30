<script setup lang="ts">
import { UsersApi, type UserRead } from '@/api';
import { get_access_token, get_api_configuration } from '@/services/api';
import { isAxiosError } from 'axios';
import { onMounted, ref } from 'vue';
import { useAppNotification } from '@/composables/useAppNotification';
import AppContainer from '@/components/generic/AppContainer.vue';
import AppPageHeader from '@/components/generic/AppPageHeader.vue';
import UserResult from '@/components/admin/UserResult.vue';

const { notify } = useAppNotification();

const config = get_api_configuration(
    get_access_token()
);

const usersApi = new UsersApi(config);

const isLoading = ref(true);

const users = ref<UserRead[]>([]);

const fetchUsers = async () => {
    try {
        const usersResponse = await usersApi.getAllUsers();
        users.value = usersResponse.data.items ?? [];
    } catch (e) {
        if (isAxiosError(e) && !!e.response?.data) {
            notify({
                title: 'Oops!',
                description: e.response.data?.detail,
                icon: 'material-symbols:error-outline-rounded',
            });
        } else {
            console.error('An unknown error occurred:', e);
            notify({
                title: 'Something went wrong',
                description: String(e),
                icon: 'material-symbols:error-outline-rounded',
            });
        }
    }
}

onMounted(async () => {
    isLoading.value = true;

    await fetchUsers();

    isLoading.value = false;
});
</script>

<template>
    <AppContainer is="main">
        <AppPageHeader>
            <template #title>
                Manage Instance
            </template>
            <template #description>
                Manage this instance of tunesynctool.
            </template>
        </AppPageHeader>
        <div class="flex flex-col gap-3">
            <div class="flex items-center gap-3 w-full mb-3 mt-8">
                <h2 class="text-2xl">Users</h2>
                <hr class="flex-1 border-zinc-700 border-0.5 ms-5" />
            </div>
            <template v-if="users.length > 0">
                <UserResult :user v-for="user in users" :key="user.id" />
            </template>
            <p class="text-sm text-zinc-400 font-normal" v-else>Unable to list users. Try reloading the page.</p>
        </div>
        <div class="text-sm text-zinc-700 py-5 flex flex-col gap-2 font-medium">
            <p>Certain configuration options cannot be changed during runtime. Refer to your compose file for further configuration options.</p>
        </div>
    </AppContainer>
</template>