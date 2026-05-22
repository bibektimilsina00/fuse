import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ProtectedRoute, PublicRoute, AppLayout } from '@/shared/components'
import { APP_ROUTES } from '@/shared/constants/routes'
import { Login, Register, ForgotPassword, ResetPassword } from '@/features/auth'
import { Dashboard } from '@/features/dashboard'
import { Settings } from '@/features/settings'
import { Showcase } from '@/features/showcase'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public auth pages */}
        <Route element={<PublicRoute />}>
          <Route path={APP_ROUTES.LOGIN} element={<Login />} />
          <Route path={APP_ROUTES.REGISTER} element={<Register />} />
          <Route path={APP_ROUTES.FORGOT_PASSWORD} element={<ForgotPassword />} />
          <Route path={APP_ROUTES.RESET_PASSWORD} element={<ResetPassword />} />
        </Route>

        {/* Protected app pages */}
        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route path={APP_ROUTES.DASHBOARD} element={<Dashboard />} />
            <Route path={APP_ROUTES.SETTINGS} element={<Settings />} />
          </Route>
        </Route>

        {/* Showcase page - public but using AppLayout */}
        <Route element={<AppLayout />}>
          <Route path={APP_ROUTES.SHOWCASE} element={<Showcase />} />
        </Route>

        {/* Redirects */}
        <Route path="/" element={<Navigate to={APP_ROUTES.DASHBOARD} replace />} />
        <Route path="*" element={<Navigate to={APP_ROUTES.DASHBOARD} replace />} />
      </Routes>
    </BrowserRouter>
  )
}

