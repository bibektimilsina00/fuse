import type { Metadata } from 'next'
import { MarketingNav, MarketingFooter } from '@/features/marketing'
import { Container } from '@/shared/components/Container'

export const metadata: Metadata = {
  title: 'Data Deletion',
  description: 'How to delete your RunMyCrew account and associated data.',
}

const CONTACT_EMAIL = 'support@runmycrew.com'

export default function DataDeletionPage() {
  return (
    <>
      <MarketingNav />
      <main>
        <section className="pb-12 pt-[120px] sm:pt-[170px]">
          <Container className="max-w-[760px] px-7">
            <p className="m-0 text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
              Legal
            </p>
            <h1 className="m-0 mt-3 text-[clamp(32px,4vw,48px)] font-[560] leading-[1.1] tracking-[-0.022em] text-foreground">
              Data Deletion
            </h1>
          </Container>
        </section>

        <section className="pb-24">
          <Container className="max-w-[760px] px-7">
            <article className="prose prose-invert max-w-none text-[15px] leading-[1.7]">
              <p>
                You can permanently delete your RunMyCrew account and all associated
                data at any time. This page covers two paths: in-product self-serve
                and email request.
              </p>

              <h2>1. Self-serve (recommended)</h2>
              <ol>
                <li>Sign in at <a href="https://app.runmycrew.com">app.runmycrew.com</a>.</li>
                <li>Open <strong>Settings → Account</strong>.</li>
                <li>Click <strong>Delete account</strong> and confirm.</li>
              </ol>
              <p>
                Deletion is immediate. Workspaces you own, workflows, run history,
                knowledge bases, and connected OAuth credentials are removed from the
                database within minutes. Backups containing the deleted data roll off
                within 30 days.
              </p>

              <h2>2. Email request</h2>
              <p>
                If you cannot sign in, email{' '}
                <a href={`mailto:${CONTACT_EMAIL}?subject=Account deletion request`}>
                  {CONTACT_EMAIL}
                </a>{' '}
                from the address registered with your account. Include:
              </p>
              <ul>
                <li>The email address of the account to delete.</li>
                <li>Confirmation that you want all associated data removed.</li>
              </ul>
              <p>
                We will respond within 7 days to confirm deletion. The full process
                completes within 30 days.
              </p>

              <h2>3. Meta / Facebook / Instagram</h2>
              <p>
                If you connected RunMyCrew to a Meta account (Facebook, Instagram,
                WhatsApp, or Lead Ads) and want to revoke that specific connection
                without deleting your RunMyCrew account, you can also disconnect from
                inside Meta:
              </p>
              <ol>
                <li>Go to{' '}
                  <a
                    href="https://www.facebook.com/settings?tab=business_tools"
                    target="_blank"
                    rel="noopener"
                  >
                    Facebook Settings → Business Integrations
                  </a>.
                </li>
                <li>Find <strong>RunMyCrew</strong> and click <strong>Remove</strong>.</li>
              </ol>
              <p>
                This revokes the OAuth grant on Meta&rsquo;s side. RunMyCrew will mark
                the credential as disconnected on its next webhook delivery; you can
                also remove the credential explicitly inside the product UI under
                Credentials.
              </p>

              <h2>4. What is deleted</h2>
              <ul>
                <li>Account profile (email, name, password hash, avatar).</li>
                <li>All workspaces you own and their workflows, run history, knowledge bases.</li>
                <li>All OAuth tokens and API keys you stored.</li>
                <li>Workspace memberships, invites you issued.</li>
              </ul>
              <p>
                What is <em>not</em> deleted: anonymized operational logs (no personal
                identifiers), invoices required for tax records (retained per legal
                obligation), and workspaces owned by other users where you were a
                guest member (those continue under the owner&rsquo;s control).
              </p>

              <h2>5. Contact</h2>
              <p>
                Questions: <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>.
              </p>
            </article>
          </Container>
        </section>
      </main>
      <MarketingFooter />
    </>
  )
}
