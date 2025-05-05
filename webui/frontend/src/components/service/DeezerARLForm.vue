<script setup lang="ts">
import * as zod from 'zod';
import { isAxiosError } from 'axios';
import { useForm } from 'vee-validate';
import { toTypedSchema } from '@vee-validate/zod';
import { DeezerApi } from '@/api';
import { computed } from 'vue';
import AppFormSpacer from '../form/AppFormSpacer.vue';
import AppField from '../form/AppField.vue';
import AppButton from '../button/AppButton.vue';
import { Icon } from '@iconify/vue';
import { get_authenticated_api_configuration } from '@/services/api';

const schema = zod.object({
  arl: zod.string().min(8, 'ARL is required')
});

const { defineField, handleSubmit, errors, isFieldValid, setFieldError } = useForm({
  initialValues: {
    arl: ''
  },
  validationSchema: toTypedSchema(schema),
});

const [arl, usernameAttributes] = defineField('arl');

const onSubmit = handleSubmit(async (values) => {
  const { arl } = values;

  const config = get_authenticated_api_configuration();
  const deezerApi = new DeezerApi(config);

  try {
    await deezerApi.setDeezerARL({
      arl: arl,
    });

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
  setFieldError('arl', message);
}

const isFormInvalid = computed(() => {
  return !isFieldValid('arl');
});

const emit = defineEmits(['linked']);
</script>

<template>
  <form @submit.prevent="onSubmit" novalidate class="mt-3 flex gap-3">
    <AppFormSpacer direction="row" class="flex-1">
      <AppField placeholder="ARL" label="ARL" name="arl" type="password" autocomplete="off" hint="Your ARL cookie"
        v-model="arl" v-bind="usernameAttributes" :error="errors.arl" />
      <AppButton type="submit" :disabled="isFormInvalid" class="h-min my-auto whitespace-nowrap">
        <Icon icon="material-symbols:add-link-rounded" class="inline-block text-2xl me-3" />LINK ACCOUNT
      </AppButton>
    </AppFormSpacer>
  </form>
</template>
