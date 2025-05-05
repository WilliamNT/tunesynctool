<script setup lang="ts">
import * as zod from 'zod';
import { isAxiosError } from 'axios';
import { useForm } from 'vee-validate';
import { toTypedSchema } from '@vee-validate/zod';
import { SubsonicApi, type ProviderRead } from '@/api';
import { computed } from 'vue';
import AppFormSpacer from '../form/AppFormSpacer.vue';
import AppField from '../form/AppField.vue';
import AppButton from '../button/AppButton.vue';
import { Icon } from '@iconify/vue';
import { get_authenticated_api_configuration } from '@/services/api';

const props = defineProps<{
  provider: ProviderRead;
}>();

const schema = zod.object({
  username: zod.string().min(1, 'Username is required'),
  password: zod.string().min(1, 'Password is required')
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

const onSubmit = handleSubmit(async (values) => {
  const { username, password } = values;

  const config = get_authenticated_api_configuration();
  const subsonicApi = new SubsonicApi(config);

  try {
    await subsonicApi.setSubsonicCredentials({
      username: username,
      password: password
    })

    emit('linked');
  } catch (e) {
    if (isAxiosError(e)) {
      switch (e.response?.status) {
        case 401:
          setErrorForAllFields('Invalid session, please sign in again');
          break;
        case 422:
          console.error('Invalid request payload (got a 422)', e.response.data);
          setErrorForAllFields('Invalid request payload');
          break;
        default:
          console.error('Error linking account:', e);
          setErrorForAllFields('An unknown error occurred while linking the account');
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

const emit = defineEmits(['linked']);
</script>

<template>
  <form @submit.prevent="onSubmit" novalidate class="mt-3">
    <AppFormSpacer direction="row">
      <AppField placeholder="Username" label="Username" name="username" type="email"
        hint="The username or email you use to sign in to your Subsonic compatible instance" v-model="username"
        v-bind="usernameAttributes" :error="errors.username" />
      <AppField placeholder="Password" label="Password" name="password"
        hint="The password you use to sign in to your Subsonic compatible instance" type="password" v-model="password"
        v-bind="passwordAttributes" :error="errors.password" />
      <AppButton type="submit" :disabled="isFormInvalid" class="h-min my-auto whitespace-nowrap">
        <Icon icon="material-symbols:add-link-rounded" class="inline-block text-2xl me-3" />LINK ACCOUNT
      </AppButton>
    </AppFormSpacer>
    <p class="mt-3 text-sm text-zinc-500 font-normal flex items-center">
      <Icon icon="material-symbols:info-outline-rounded" class="me-1" />Additional connection settings can be configured
      via environmental variables.
    </p>
  </form>
</template>
