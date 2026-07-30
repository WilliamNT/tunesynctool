<script setup lang="ts">
import AppButton from '@/components/button/AppButton.vue';
import AppCard from '@/components/card/AppCard.vue';
import AppField from '@/components/form/AppField.vue';
import AppFormSpacer from '@/components/form/AppFormSpacer.vue';
import { UsersApi } from '@/api';
import { get_api_configuration } from '@/services/api';
import { useForm } from 'vee-validate';
import { toTypedSchema } from '@vee-validate/zod';
import * as zod from 'zod';
import { isAxiosError } from 'axios';
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import AppContainer from '@/components/generic/AppContainer.vue';
import { useAppNotification } from '@/composables/useAppNotification';

const { notify } = useAppNotification();

const schema = zod.object({
  username: zod.string({
    required_error: 'You have to provide a username',
    message: 'Username must be a valid email'
  }).min(3, 'Username must be at least 3 characters long')
    .max(255, 'Username must be at most 255 characters long'),

  password: zod.string({
    required_error: 'You have to provide a password',
    message: 'Password must be at least 8 characters long'
  }).min(8, { message: 'Password must be at least 8 characters long' })
    .max(255, 'Password must be at most 255 characters long')
});

const { defineField, handleSubmit, errors, isFieldValid, setFieldError } = useForm({
  initialValues: {
    username: '',
    password: ''
  },
  validationSchema: toTypedSchema(schema),
});

const [username, usernameAttributes] = defineField('username');
const [password, passwordAttributes] = defineField('password');

const router = useRouter();

const onSubmit = handleSubmit(async (values) => {
  const { username, password } = values;

  const config = get_api_configuration();
  const usersApi = new UsersApi(config);

  try {
    await usersApi.createUser({ username, password });
    router.push({ name: 'login' });
  } catch (e) {
    if (isAxiosError(e)) {
      switch (e.response?.status) {
        case 400:
          setErrorForAllFields(e.response.data.detail || 'Something went wrong');
          break;
        case 422:
          console.error('Invalid request payload (got a 422)', e.response.data);
          setErrorForAllFields('Invalid request payload');
          break;
        case 403:
          notify({
            title: 'An error occured',
            description: e.response.data?.detail,
            icon: 'material-symbols:error-outline-rounded',
          });
      }
    } else {
      console.error('An unknown error occurred:', e);
      notify({
        title: 'Something went wrong',
        description: String(e),
        icon: 'material-symbols:error-outline-rounded',
      });
    }
  }
});

function setErrorForAllFields(message: string) {
  setFieldError('username', message);
  setFieldError('password', message);
}

const isFormInvalid = computed(() => {
  return !isFieldValid('username') || !isFieldValid('password');
});
</script>

<template>
  <AppContainer is="main">
    <AppCard class="max-w-md m-auto p-5">
      <form @submit.prevent="onSubmit" novalidate>
        <h1 class="text-4xl text-white text-center font-normal">
          Sign Up
        </h1>
        <hr class="border-zinc-700 border-0.5 mb-5 mt-6">
        <AppFormSpacer>
          <AppField placeholder="Username" label="Username" name="username" type="email" v-model="username"
            v-bind="usernameAttributes" :error="errors.username" />
          <AppField placeholder="Password" label="Password" name="password" type="password" v-model="password"
            v-bind="passwordAttributes" :error="errors.password" />
          <AppButton type="submit" :disabled="isFormInvalid">Sign Up</AppButton>
          <p class="font-normal text-md text-center">
            or
            <RouterLink :to="{ name: 'login' }" class="text-lime-400 hover:text-lime-500">sign in</RouterLink>
          </p>
        </AppFormSpacer>
      </form>
    </AppCard>
  </AppContainer>
</template>
