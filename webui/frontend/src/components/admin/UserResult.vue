<script setup lang="ts">
import AppCard from '../card/AppCard.vue';
import AppConfirmDialog from '../generic/AppConfirmDialog.vue';
import { Icon } from '@iconify/vue/dist/iconify.js';
import UserAvatar from '../image/UserAvatar.vue';
import { UsersApi, type UserRead } from '@/api/index.ts';
import { ref } from 'vue';
import AppButton from '../button/AppButton.vue';
import { get_access_token, get_api_configuration } from '@/services/api.ts';
import { isAxiosError } from 'axios';
import { useAppNotification } from '@/composables/useAppNotification.ts';

const props = defineProps<{
  user: UserRead;
}>();

const emit = defineEmits(['deleted']);

const isDeletionLoading = ref(false);
const isConfirmDeleteOpen = ref(false);

const { notify } = useAppNotification();

const config = get_api_configuration(
    get_access_token()
);

const usersApi = new UsersApi(config);

const confirmDeleteUser = async () => {
  isDeletionLoading.value = true;

  try {
      await usersApi.deleteUser(props.user.id);

      emit('deleted');
      
      notify({
          title: 'Success',
          description: 'User deleted successfully',
          icon: 'material-symbols:check-circle-outline-rounded',
      });

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

  isDeletionLoading.value = false;
}
</script>

<template>
  <AppCard class="flex gap-4">
    <UserAvatar />
    <div class="flex flex-col gap-0.5 flex-1">
      <h3 class="text-xl">{{ user.username }}</h3>
      <ul class="flex gap-2 list-none p-0 m-0 text-zinc-400 font-normal items-center">
        <li class="relative pl-3.5 first:pl-0 before:content-['•'] before:absolute before:left-0 first:before:content-[''] before:text-zinc-500 truncate">
          <template v-if="user.is_admin">
            <Icon icon="material-symbols:settings-outline-rounded" class="inline-block me-1 text-lg text-green-200" />
            <span class="text-green-300" title="This user is an administrator.">Admin</span>
          </template>
          <template v-else>
            <Icon icon="material-symbols:account-circle-outline" class="inline-block me-1 text-lg text-blue-200" />
            <span class="text-blue-200">Regular user</span>
          </template>
        </li>
        <li class="relative pl-3.5 first:pl-0 before:content-['•'] before:absolute before:left-0 first:before:content-[''] before:text-zinc-500 truncate">
          User ID: {{ user.id }}
        </li>
      </ul>
    </div>
    <div class="flex gap-3 ms-auto items-center">
      <AppButton type="button" :disabled="isDeletionLoading" tone="negative"  @click="isConfirmDeleteOpen = true">
        <Icon icon="material-symbols:delete-outline-rounded" class="inline-block text-2xl me-3" />REMOVE USER
      </AppButton>
    </div>
    <AppConfirmDialog
      v-model:open="isConfirmDeleteOpen"
      title="Delete user?"
      :message="`Delete ${props.user.username}? This action cannot be undone.`"
      confirm-text="Delete"
      confirm-tone="negative"
      @confirm="confirmDeleteUser"
    />
  </AppCard>
</template>