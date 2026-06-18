import { AuthShell } from '../components/AuthShell'
import { ForgotPasswordForm } from '../components/ForgotPasswordForm'

export function ForgotPassword() {
  return (
    <AuthShell backHref="/login" backLabel="Back to login">
      <ForgotPasswordForm />
    </AuthShell>
  )
}
