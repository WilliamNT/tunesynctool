import { is_access_token_set } from '@/services/api';
import { createRouter, createWebHistory } from 'vue-router';

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            name: 'home',
            component: () => import('../views/HomeView.vue'),
        },
        {
          path: '/login',
          name: 'login',
          component: () => import('../views/LoginView.vue'),
        },
        {
          path: '/search',
          name: 'search',
          component: () => import('../views/SearchView.vue'),
        },
        {
          path: '/tasks',
          name: 'tasks',
          component: () => import('../views/TasksView.vue'),
        },
        {
          path: '/accounts',
          name: 'accounts',
          component: () => import('../views/AccountsView.vue'),
        },
        {
          path: '/login',
          name: 'login',
          component: () => import('../views/LoginView.vue'),
        },
        {
          path: '/register',
          name: 'register',
          component: () => import('../views/RegistrationView.vue'),
        },
        {
          path: '/playlists',
          redirect: '/'
        },
        {
          path: '/playlists/:id',
          name: 'playlist',
          component: () => import('../views/PlaylistView.vue'),
        }
    ],
});

router.beforeEach((to, from, next) => {
  const isAuthenticated = is_access_token_set();
  const unauthenticatedRoutes = ['login', 'register'];

  if (to.name && unauthenticatedRoutes.includes(to.name as string) && isAuthenticated) {
    next({ name: 'home' });
  } else if (!isAuthenticated && !unauthenticatedRoutes.includes(to.name as string)) {
    next({ name: 'login' });
  } else {
    next();
  }
});

export default router;
