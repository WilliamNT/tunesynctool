<script setup lang="ts">
import { get_access_token, get_api_configuration } from '@/services/api';
import { UsersApi, type UserRead } from '@/api';
import { onMounted, ref } from 'vue';

const config = get_api_configuration(
  get_access_token()
);

const usersApi = new UsersApi(config);

onMounted(async () => {
  const response = await usersApi.getAuthenticatedUser();

  me.value = response.data;
});

const me = ref<UserRead>();
</script>

<template>
  <h1>Tasks</h1>
</template>
