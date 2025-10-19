<script setup lang="ts">
import AppButton from '@/components/button/AppButton.vue';
import AppCard from '@/components/card/AppCard.vue';
import AppField from '@/components/form/AppField.vue';
import AppFormSpacer from '@/components/form/AppFormSpacer.vue';
import { AuthenticationApi } from '@/api';
import { set_access_token, get_api_configuration } from '@/services/api';
import { useForm } from 'vee-validate';
import { toTypedSchema } from '@vee-validate/zod';
import * as zod from 'zod';
import { isAxiosError } from 'axios';
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import AppContainer from '@/components/generic/AppContainer.vue';
import AppWarningBar from '@/components/generic/AppWarningBar.vue';

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
  const authApi = new AuthenticationApi(config);

  try {
    const response = await authApi.getToken(username, password);

    const token = response.data.access_token;
    set_access_token(token);

    router.push({ name: 'home' });
  } catch (e) {
    if (isAxiosError(e)) {
      switch (e.response?.status) {
        case 401:
          setErrorForAllFields('Invalid username or password');
          break;
        case 422:
          console.error('Invalid request payload (got a 422)', e.response.data);
          setErrorForAllFields('Invalid request payload');
          break;
      }
    } else {
      console.error('An unknown error occurred:', e);
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
    <AppWarningBar message="This app is still under heavy development. Please treat this as a preview/alpha version. GitHub issues are welcome." />
    <AppCard class="max-w-md m-auto p-5">
      <form @submit.prevent="onSubmit" novalidate>
        <h1 class="text-4xl text-white text-center font-normal">
          Sign In
        </h1>
        <hr class="border-zinc-700 border-0.5 mb-5 mt-6">
        <AppFormSpacer>
          <AppField placeholder="Username" label="Username" name="username" type="email" v-model="username"
            v-bind="usernameAttributes" :error="errors.username" />
          <AppField placeholder="Password" label="Password" name="password" type="password" v-model="password"
            v-bind="passwordAttributes" :error="errors.password" />
          <AppButton type="submit" :disabled="isFormInvalid">Sign In</AppButton>
          <p class="font-normal text-md text-center">
            or
            <RouterLink :to="{ name: 'register' }" class="text-lime-400 hover:text-lime-500">sign up</RouterLink>
          </p>
        </AppFormSpacer>
      </form>
    </AppCard>
  </AppContainer>
</template>
