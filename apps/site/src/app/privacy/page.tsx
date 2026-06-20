import type { Metadata } from 'next'
import { MarketingNav, MarketingFooter } from '@/features/marketing'
import { Container } from '@/shared/components/Container'

export const metadata: Metadata = {
  title: 'Privacy Policy',
  description: 'How RunMyCrew collects, uses, and protects your data.',
}

const LAST_UPDATED = 'June 20, 2026'
const CONTACT_EMAIL = 'support@runmycrew.com'

export default function PrivacyPage() {
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
              Privacy Policy
            </h1>
            <p className="mt-4 text-[14px] text-muted-foreground">Last updated: {LAST_UPDATED}</p>
          </Container>
        </section>

        <section className="pb-24">
          <Container className="max-w-[760px] px-7">
            <article className="prose prose-invert max-w-none text-[15px] leading-[1.7]">
              <p>
                RunMyCrew (&ldquo;we&rdquo;, &ldquo;us&rdquo;) operates the automation
                platform at runmycrew.com (the &ldquo;Service&rdquo;). This policy
                explains what we collect, why, how we use it, and the choices you have.
                By using the Service you agree to this policy.
              </p>

              <h2>1. Information we collect</h2>
              <ul>
                <li>
                  <strong>Account data</strong> — email address, name, password hash,
                  and (if you sign in with Google) the basic OpenID profile fields
                  Google returns: name, picture, email-verified status.
                </li>
                <li>
                  <strong>Workspace data</strong> — workflow definitions, run history,
                  knowledge bases, and any content you upload to the Service.
                </li>
                <li>
                  <strong>Connected-app credentials</strong> — OAuth tokens and API keys
                  you provide so RunMyCrew can call third-party APIs on your behalf
                  (GitHub, Slack, Google, Meta, Notion, etc.). Tokens are encrypted at
                  rest with AES-256 (Fernet).
                </li>
                <li>
                  <strong>Operational logs</strong> — IP address, user-agent, request
                  paths, error traces, and timing. Retained for up to 30 days for
                  security, debugging, and abuse prevention.
                </li>
              </ul>

              <h2>2. How we use information</h2>
              <ul>
                <li>To operate, secure, and improve the Service.</li>
                <li>To authenticate you and authorize access to your workspaces.</li>
                <li>
                  To execute the workflows you build — including making API calls to the
                  third-party services you have connected.
                </li>
                <li>
                  To send transactional email (password resets, workspace invites).
                  We do not send marketing email without explicit opt-in.
                </li>
                <li>To comply with legal obligations and enforce our Terms.</li>
              </ul>

              <h2>3. Third-party services</h2>
              <p>
                When you connect a third-party service via OAuth (for example Google),
                we receive only the scopes you grant on the consent screen. We do not
                read, store, or transmit content beyond what is required to execute the
                workflows you have configured. Specifically:
              </p>
              <ul>
                <li>
                  <strong>Google APIs.</strong> Use of information received from Google
                  APIs adheres to the{' '}
                  <a
                    href="https://developers.google.com/terms/api-services-user-data-policy"
                    target="_blank"
                    rel="noopener"
                  >
                    Google API Services User Data Policy
                  </a>
                  , including the Limited Use requirements. We use Google data only to
                  provide and improve user-facing features that the user explicitly
                  invoked. We do not transfer Google data for serving ads, do not use it
                  for unrelated purposes, and do not allow humans to read it except with
                  your explicit consent, for security, or as required by law.
                </li>
                <li>
                  <strong>Meta / Instagram / WhatsApp.</strong> When you connect a Meta
                  account, we store the access token and trigger webhooks for the events
                  you subscribe to. We do not share Meta data with any other party.
                </li>
              </ul>

              <h2>4. Data sharing</h2>
              <p>We do not sell or rent your personal data. We share data only:</p>
              <ul>
                <li>With infrastructure providers required to run the Service (hosting, database, email delivery, analytics).</li>
                <li>When you direct us to (for example, sending a workflow output to a third-party app).</li>
                <li>When required by law, subpoena, or court order.</li>
              </ul>

              <h2>5. Data retention &amp; deletion</h2>
              <p>
                Workspace data is retained while your account is active. You can delete
                a workspace, a workflow, or a connected credential at any time from the
                product UI. To delete your entire account and all associated data, see
                our{' '}
                <a href="/data-deletion">Data Deletion</a> page or email{' '}
                <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>. We honor
                deletion requests within 30 days. Operational logs roll off
                automatically after 30 days.
              </p>

              <h2>6. Security</h2>
              <p>
                All traffic is TLS 1.2+. Passwords are hashed with Argon2id. OAuth
                tokens and API keys are encrypted at rest with AES-256. Access to
                production systems is restricted by SSH keys and audit-logged.
                We do not store credit card information; payments are processed by
                Stripe.
              </p>

              <h2>7. International users</h2>
              <p>
                The Service is operated from infrastructure in the European Union and
                the United States. If you are located outside these regions, you
                acknowledge that data you submit may be transferred to and processed
                in those regions.
              </p>

              <h2>8. Children</h2>
              <p>
                The Service is not directed to children under 16. We do not knowingly
                collect personal information from anyone under 16.
              </p>

              <h2>9. Changes</h2>
              <p>
                We may update this policy. Material changes will be announced at least
                30 days in advance via the product UI or email.
              </p>

              <h2>10. Contact</h2>
              <p>
                Questions about this policy or about your data:{' '}
                <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>.
              </p>
            </article>
          </Container>
        </section>
      </main>
      <MarketingFooter />
    </>
  )
}
