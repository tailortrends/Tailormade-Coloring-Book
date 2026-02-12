<script setup lang="ts">
import { useAuthStore } from '@/store/auth'

const auth = useAuthStore()
</script>

<template>
  <nav class="navbar bg-base-100 border-b-2 border-base-300 px-4 sticky top-0 z-40">
    <div class="navbar-start">
      <router-link to="/" class="flex items-center gap-2 no-underline">
        <span class="text-3xl">🎨</span>
        <span class="font-display text-xl text-primary hidden sm:block">TailorMade</span>
      </router-link>
    </div>

    <div class="navbar-end gap-2">
      <router-link
        v-if="auth.isAuthenticated"
        to="/gallery"
        class="btn btn-ghost btn-sm rounded-full font-body hidden sm:flex"
      >
        My Books
      </router-link>

      <template v-if="auth.isAuthenticated">
        <div class="dropdown dropdown-end">
          <button tabindex="0" class="btn btn-ghost btn-circle avatar">
            <div class="w-10 rounded-full">
              <img
                v-if="auth.photoURL"
                :src="auth.photoURL"
                :alt="auth.displayName"
                class="rounded-full"
              />
              <div v-else class="bg-primary text-white flex items-center justify-center h-full rounded-full font-display text-lg">
                {{ auth.displayName[0] }}
              </div>
            </div>
          </button>
          <ul tabindex="0" class="menu menu-sm dropdown-content bg-base-100 rounded-3xl z-50 mt-3 w-48 p-2 shadow-lg border-2 border-base-300">
            <li><router-link to="/gallery">My Books</router-link></li>
            <li><button @click="auth.signOut()">Sign Out</button></li>
          </ul>
        </div>
      </template>

      <button
        v-else
        class="btn btn-primary btn-kid"
        @click="auth.signInWithGoogle()"
      >
        Sign In
      </button>
    </div>
  </nav>
</template>
