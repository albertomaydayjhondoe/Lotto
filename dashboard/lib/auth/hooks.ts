/**
 * Authentication hooks for React components.
 */

'use client';

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { authApi, LoginCredentials, UserMe } from './api';

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: UserMe | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  refreshAccessToken: () => Promise<void>;
  fetchUser: () => Promise<void>;
  hasRole: (role: string) => boolean;
  hasScope: (scope: string) => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,
      isLoading: false,

      login: async (credentials: LoginCredentials) => {
        set({ isLoading: true });
        try {
          const tokens = await authApi.login(credentials);
          set({
            accessToken: tokens.access_token,
            refreshToken: tokens.refresh_token,
            isAuthenticated: true,
          });

          // Fetch user info
          await get().fetchUser();
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      logout: async () => {
        const { refreshToken, accessToken } = get();
        if (refreshToken && accessToken) {
          try {
            await authApi.logout(refreshToken, accessToken);
          } catch (error) {
            console.error('Logout error:', error);
          }
        }
        
        set({
          accessToken: null,
          refreshToken: null,
          user: null,
          isAuthenticated: false,
        });
      },

      refreshAccessToken: async () => {
        const { refreshToken } = get();
        if (!refreshToken) {
          throw new Error('No refresh token available');
        }

        try {
          const tokens = await authApi.refresh(refreshToken);
          set({
            accessToken: tokens.access_token,
            refreshToken: tokens.refresh_token,
          });
        } catch (error) {
          // Refresh failed, logout user
          await get().logout();
          throw error;
        }
      },

      fetchUser: async () => {
        const { accessToken } = get();
        if (!accessToken) return;

        try {
          const user = await authApi.getMe(accessToken);
          set({ user, isLoading: false });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      hasRole: (role: string) => {
        const { user } = get();
        return user?.role === role;
      },

      hasScope: (scope: string) => {
        const { user } = get();
        if (!user) return false;

        // Admin has all scopes
        if (user.scopes.includes('all')) return true;

        // Check exact match
        if (user.scopes.includes(scope)) return true;

        // Check wildcard match
        const [prefix] = scope.split(':');
        if (user.scopes.includes(`${prefix}:*`)) return true;

        return false;
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

export function useAuth() {
  return useAuthStore();
}
