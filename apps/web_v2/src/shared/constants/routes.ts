/**
 * Centralized Application Routes (Frontend)
 */
export const APP_ROUTES = {
  LOGIN: '/login',
  REGISTER: '/register',
  FORGOT_PASSWORD: '/forgot-password',
  RESET_PASSWORD: '/reset-password',
  DASHBOARD: '/dashboard',
  SETTINGS: '/settings',
  SHOWCASE: '/showcase',
} as const

export type AppRoute = typeof APP_ROUTES[keyof typeof APP_ROUTES]

/**
 * Centralized API Routes (Backend Endpoints relative to base url '/api/v1')
 */
export const API_ROUTES = {
  LOGIN: '/auth/login',
  REGISTER: '/auth/register',
  ME: '/auth/me',
  FORGOT_PASSWORD: '/auth/forgot-password',
  RESET_PASSWORD: '/auth/reset-password',
} as const

export type ApiRoute = typeof API_ROUTES[keyof typeof API_ROUTES]
