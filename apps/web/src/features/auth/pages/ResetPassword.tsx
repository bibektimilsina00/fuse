import { AuthShell } from '../components/AuthShell'
import { ResetPasswordForm } from '../components/ResetPasswordForm'

export function ResetPassword() {
  return (
    <AuthShell backHref="/login" backLabel="Back to login">
      <ResetPasswordForm />
    </AuthShell>
  )
}
