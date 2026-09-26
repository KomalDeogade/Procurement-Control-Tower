/**
 * Authentication service – login, logout, current user.
 */

import api from './api';
import type { AuthTokens, User } from '../types';

export const authService = {
  async login(username: string, password: string): Promise<AuthTokens> {
    const { data } = await api.post<AuthTokens>('/auth/login', { username, password });
    localStorage.setItem('access_token', data.access_token);
    return data;
  },

  logout(): void {
    localStorage.removeItem('access_token');
    window.location.href = '/login';
  },

  async getCurrentUser(): Promise<User> {
    const { data } = await api.get<User>('/auth/me');
    return data;
  },

  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token');
  },
};
