import type { Metadata } from 'next'
import { MarketingNav, MarketingFooter } from '@/features/marketing'
import { Container } from '@/shared/components/Container'

export const metadata: Metadata = {
  title: 'Data Deletion',
  description:
    'How to delete your RunMyCrew account, a single integration, or revoke a Meta / Google connection — self-serve or by request.',
}

const PRIVACY_EMAIL = 'privacy@runmycrew.com'
const SUPPORT_EMAIL = 'support@runmycrew.com'

export default function DataDeletionPage() {
  return (
    <>
      <MarketingNav />
      <main>
        <section className="pb-12 pt-[120px] sm:pt-[170px]">
          <Container className="max-w-[760px] px-7">
            <p className="m-0 text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
              Legal · Data Deletion
            </p>
            <h1 className="m-0 mt-3 text-[clamp(32px,4vw,48px)] font-[560] leading-[1.1] tracking-[-0.022em] text-foreground">
              Data Deletion
            </h1>
            <p className="mt-4 text-[14px] text-muted-foreground">
              Three paths: self-serve in product, email request, or revoke a
              specific Meta / Google connection.
            </p>
          </Container>
        </section>

        <section className="pb-24">
          <Container className="max-w-[760px] px-7">
            <article className="prose prose-invert max-w-none text-[15px] leading-[1.7]">
              <p>
                You can delete your RunMyCrew account, a single workspace, a
                single workflow, or a single connected credential at any time.
                We honor every deletion within 30 days; most are immediate. This
                page documents the exact procedure for each option, including
                the Meta-mandatory data deletion endpoint required for app
                review.
              </p>

              <h2 id="self-serve">1. Self-serve (recommended)</h2>
              <ol>
                <li>
                  Sign in at{' '}
                  <a href="https://app.runmycrew.com">app.runmycrew.com</a>.
                </li>
                <li>
                  Open <strong>Settings → Account</strong>.
                </li>
                <li>
                  Click <strong>Delete account</strong> and confirm.
                </li>
              </ol>
              <p>
                Deletion is immediate. Workspaces you own, their workflows, run
                history, knowledge bases, and connected OAuth credentials are
                removed from the database within minutes. Encrypted backups
                containing the deleted data roll off automatically within 30
                days.
              </p>

              <h2 id="email">2. Email request</h2>
              <p>
                If you cannot sign in (locked out, lost 2FA, deceased account
                holder, etc.), email{' '}
                <a
                  href={`mailto:${PRIVACY_EMAIL}?subject=${encodeURIComponent('Account deletion request')}`}
                >
                  {PRIVACY_EMAIL}
                </a>{' '}
                from the address registered with your account (or include a
                photo ID and a death certificate where applicable). Include:
              </p>
              <ul>
                <li>The email address of the account to delete.</li>
                <li>Confirmation that you want all associated data removed.</li>
                <li>
                  Any specific workspaces or workflows you want preserved
                  (uncommon — most users opt to delete everything).
                </li>
              </ul>
              <p>
                We confirm receipt within 3 business days and complete the
                deletion within 30 days.
              </p>

              <h2 id="meta">3. Meta / Facebook / Instagram / WhatsApp disconnect</h2>
              <p>
                This is the dedicated <strong>data deletion callback</strong>{' '}
                that Meta App Review requires us to publish. You can also use it
                to revoke RunMyCrew&rsquo;s Meta access without deleting your
                whole RunMyCrew account.
              </p>
              <p>
                <strong>Option A — from Meta:</strong>
              </p>
              <ol>
                <li>
                  Open{' '}
                  <a
                    href="https://www.facebook.com/settings?tab=business_tools"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Facebook Settings → Business Integrations
                  </a>
                  .
                </li>
                <li>
                  Find <strong>RunMyCrew</strong> and click <strong>Remove</strong>.
                </li>
                <li>
                  Meta will send a signed deletion callback to{' '}
                  <code>https://app.runmycrew.com/api/v1/webhooks/meta/data-deletion</code>.
                  We revoke the credential, delete the access token, and
                  invalidate any cached webhook subscription within minutes.
                </li>
              </ol>
              <p>
                <strong>Option B — from RunMyCrew:</strong> Settings → Connected
                accounts → Meta → Disconnect.
              </p>
              <p>
                <strong>Option C — by email:</strong> mail{' '}
                <a
                  href={`mailto:${PRIVACY_EMAIL}?subject=${encodeURIComponent('Meta data deletion')}`}
                >
                  {PRIVACY_EMAIL}
                </a>{' '}
                from your registered email with the Meta business account name
                or Facebook page ID. We delete within 30 days and email a
                confirmation receipt with a tracking code.
              </p>

              <h2 id="google">4. Google disconnect</h2>
              <p>
                To revoke RunMyCrew&rsquo;s Google access while keeping your
                RunMyCrew account:
              </p>
              <ol>
                <li>
                  Open{' '}
                  <a
                    href="https://myaccount.google.com/permissions"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Google Account → Third-party apps with account access
                  </a>
                  .
                </li>
                <li>
                  Find <strong>RunMyCrew</strong> and click <strong>Remove access</strong>.
                </li>
                <li>
                  Or, from RunMyCrew: Settings → Connected accounts → Google →
                  Disconnect.
                </li>
              </ol>
              <p>
                Either path revokes the OAuth grant, deletes the encrypted
                refresh token from our database, and stops any scheduled
                workflow that depends on it.
              </p>

              <h2 id="what">5. What we delete</h2>
              <ul>
                <li>Account profile (email, name, password hash, avatar URL).</li>
                <li>
                  All workspaces you own and their workflows, run history, and
                  knowledge bases.
                </li>
                <li>
                  All connected-credential rows (OAuth refresh tokens, API
                  keys, signed webhook secrets).
                </li>
                <li>
                  Workspace memberships, invites you issued, and audit log
                  entries.
                </li>
                <li>Encrypted backups within 30 days of deletion.</li>
              </ul>

              <h2 id="what-not">6. What we do not delete</h2>
              <ul>
                <li>
                  Anonymized operational metrics (no personal identifier).
                </li>
                <li>
                  Invoices retained for tax law compliance (up to 10 years per
                  applicable jurisdiction).
                </li>
                <li>
                  Workspaces owned by other users where you were a guest
                  member — those continue under the owner&rsquo;s control;
                  email the owner to be removed.
                </li>
                <li>
                  Public-only artifacts you posted to integrated services (a
                  Slack message you sent, a GitHub issue you commented on)
                  remain in those services; deletion has to be initiated there.
                </li>
              </ul>

              <h2 id="contact">7. Contact</h2>
              <p>
                Privacy / deletion questions:{' '}
                <a href={`mailto:${PRIVACY_EMAIL}`}>{PRIVACY_EMAIL}</a>
                <br />
                General support:{' '}
                <a href={`mailto:${SUPPORT_EMAIL}`}>{SUPPORT_EMAIL}</a>
              </p>
            </article>
          </Container>
        </section>
      </main>
      <MarketingFooter />
    </>
  )
}
