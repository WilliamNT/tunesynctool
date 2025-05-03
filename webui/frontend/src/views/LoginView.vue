<script setup lang="ts">
import AppButton from '@/components/button/AppButton.vue';
import AppCard from '@/components/card/AppCard.vue';
import AppField from '@/components/form/AppField.vue';
import AppFormSpacer from '@/components/form/AppFormSpacer.vue';
import AppH1 from '@/components/text/AppH1.vue';
import { AuthenticationApi } from '@/api';
import { set_access_token, get_api_configuration } from '@/services/api';
import { useForm, useIsFormValid } from 'vee-validate';
import { toTypedSchema } from '@vee-validate/zod';
import * as zod from 'zod';
import { isAxiosError } from 'axios';
import { computed } from 'vue';
import { useRouter } from 'vue-router';

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
  <main class="my-auto">
    <AppCard class="max-w-md m-auto">
      <form @submit.prevent="onSubmit" novalidate>
        <AppH1 class="text-center">Sign In</AppH1>
        <AppFormSpacer>
          <AppField placeholder="Username" label="Username" name="username" type="email" v-model="username"
            v-bind="usernameAttributes" :error="errors.username" />
          <AppField placeholder="Password" label="Password" name="password" type="password" v-model="password"
            v-bind="passwordAttributes" :error="errors.password" />
          <AppButton type="submit" class="mt-4" :disabled="isFormInvalid">Sign In</AppButton>
        </AppFormSpacer>
      </form>
    </AppCard>
  </main>
</template>
