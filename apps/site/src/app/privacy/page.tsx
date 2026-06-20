import type { Metadata } from 'next'
import { MarketingNav, MarketingFooter } from '@/features/marketing'
import { Container } from '@/shared/components/Container'

export const metadata: Metadata = {
  title: 'Privacy Policy',
  description:
    'How RunMyCrew collects, uses, protects, and shares your data — and the choices you have. Includes Google API Services User Data Policy and Meta Platform compliance.',
}

const LAST_UPDATED = 'June 20, 2026'
const EFFECTIVE_DATE = 'June 20, 2026'
const CONTACT_EMAIL = 'privacy@runmycrew.com'
const SUPPORT_EMAIL = 'support@runmycrew.com'

export default function PrivacyPage() {
  return (
    <>
      <MarketingNav />
      <main>
        <section className="pb-12 pt-[120px] sm:pt-[170px]">
          <Container className="max-w-[760px] px-7">
            <p className="m-0 text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
              Legal · Privacy
            </p>
            <h1 className="m-0 mt-3 text-[clamp(32px,4vw,48px)] font-[560] leading-[1.1] tracking-[-0.022em] text-foreground">
              Privacy Policy
            </h1>
            <p className="mt-4 text-[14px] text-muted-foreground">
              Last updated: {LAST_UPDATED} · Effective: {EFFECTIVE_DATE}
            </p>
          </Container>
        </section>

        <section className="pb-24">
          <Container className="max-w-[760px] px-7">
            <article className="prose prose-invert max-w-none text-[15px] leading-[1.7]">
              <p>
                This Privacy Policy explains how RunMyCrew (&ldquo;RunMyCrew,&rdquo;
                &ldquo;we,&rdquo; &ldquo;us&rdquo;) collects, uses, discloses, and
                protects information when you use the automation platform at{' '}
                <a href="https://runmycrew.com">runmycrew.com</a> and{' '}
                <a href="https://app.runmycrew.com">app.runmycrew.com</a>{' '}
                (collectively, the &ldquo;Service&rdquo;).
              </p>

              <p>
                <strong>Plain-language summary.</strong> We collect only what we
                need to run the Service for you, never sell your data, never use
                your data to train AI models without your explicit opt-in, and
                only access third-party APIs (Google, Meta, Slack, etc.) to
                execute the workflows you have explicitly built and authorized.
              </p>

              <h2 id="information-we-collect">1. Information we collect</h2>

              <h3>1.1 Information you provide</h3>
              <ul>
                <li>
                  <strong>Account data</strong> — email address, password hash
                  (Argon2id), full name, profile picture URL. Optional fields:
                  organization name, role.
                </li>
                <li>
                  <strong>Authentication via Google Sign-In</strong> — when you
                  sign in with Google, we receive the OpenID Connect profile
                  fields you consent to: <code>email</code>,{' '}
                  <code>email_verified</code>, <code>name</code>,{' '}
                  <code>picture</code>. We do not receive your Google password.
                </li>
                <li>
                  <strong>Workspace content</strong> — workflow definitions,
                  node configurations, run history, knowledge bases, and any
                  files or text you upload.
                </li>
                <li>
                  <strong>Connected-app credentials</strong> — OAuth refresh
                  tokens and API keys for the third-party services you connect
                  (Google, Meta, Slack, GitHub, Notion, Discord, Linear, and
                  others). All credentials are encrypted at rest with AES-256
                  (Fernet, scoped key derivation).
                </li>
                <li>
                  <strong>Billing data</strong> (paid plans) — handled by Stripe.
                  We store only the Stripe customer ID and the last 4 digits of
                  the card. We do not store full card numbers.
                </li>
                <li>
                  <strong>Support correspondence</strong> — when you email us,
                  we keep the thread for up to 24 months for context.
                </li>
              </ul>

              <h3>1.2 Information collected automatically</h3>
              <ul>
                <li>
                  <strong>Operational logs</strong> — IP address, user agent,
                  request path, response code, timing. Retained 30 days for
                  security and debugging.
                </li>
                <li>
                  <strong>Workflow run telemetry</strong> — execution
                  timestamps, step durations, success/failure status, and the
                  input/output payload of each node. You control retention
                  (free: 7 days, pro: 30 days, enterprise: configurable).
                </li>
                <li>
                  <strong>Cookies / localStorage</strong> — see our{' '}
                  <a href="/cookies">Cookie Policy</a>. We use exactly one
                  first-party authentication token stored in{' '}
                  <code>localStorage</code>; no advertising or analytics
                  third-party cookies.
                </li>
              </ul>

              <h3>1.3 Information from third parties</h3>
              <p>
                Only what the third-party API returns when executing the
                workflows you built. For example, if you connect Gmail, we
                receive the message metadata and body you specifically asked
                the workflow to read or send. We do not pre-fetch, index, or
                store third-party content beyond what is required to execute
                the current run.
              </p>

              <h2 id="how-we-use">2. How we use information</h2>
              <ul>
                <li>Operate, secure, and improve the Service.</li>
                <li>
                  Authenticate you and authorize access to your workspaces.
                </li>
                <li>
                  Execute workflows you have built — including calling
                  third-party APIs on your behalf with credentials you
                  connected.
                </li>
                <li>
                  Provide AI workflow generation (Crew AI). When you submit a
                  prompt, the prompt and the resulting workflow graph are sent
                  to the LLM provider you selected (Anthropic / OpenAI / Google
                  Gemini / etc.). We do not store prompts beyond the run history
                  setting on your plan.
                </li>
                <li>
                  Send transactional email (password resets, workspace invites,
                  security alerts) from{' '}
                  <a href="mailto:noreply@runmycrew.com">noreply@runmycrew.com</a>.
                  We do not send marketing email without explicit opt-in.
                </li>
                <li>
                  Detect and prevent abuse: rate limits, anomalous-usage
                  detection, brute-force / credential-stuffing protection.
                </li>
                <li>Comply with legal obligations and enforce our Terms.</li>
              </ul>

              <p>
                <strong>What we do NOT do.</strong>
              </p>
              <ul>
                <li>
                  We do not use your workspace content, prompts, runs, or
                  connected-account data to train any AI/ML model — neither our
                  own nor any third party&rsquo;s — without your explicit,
                  separate opt-in.
                </li>
                <li>We do not sell, rent, or trade personal data.</li>
                <li>
                  We do not show third-party advertising on the Service. No
                  ad-targeting cookies, pixels, or SDKs.
                </li>
              </ul>

              <h2 id="google-limited-use">
                3. Google API Services User Data Policy — Limited Use disclosure
              </h2>
              <p>
                RunMyCrew&rsquo;s use and transfer of information received from
                Google APIs to any other app will adhere to the{' '}
                <a
                  href="https://developers.google.com/terms/api-services-user-data-policy#additional_requirements_for_specific_api_scopes"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Google API Services User Data Policy
                </a>
                , including the <strong>Limited Use</strong> requirements.
                Specifically:
              </p>
              <ul>
                <li>
                  Google user data is used only to provide or improve
                  user-facing features that are prominent in the requesting
                  application&rsquo;s user interface.
                </li>
                <li>
                  We do not transfer Google user data to third parties except as
                  necessary to provide or improve user-facing features, comply
                  with applicable law, or as part of a merger, acquisition, or
                  sale of assets (with appropriate notice).
                </li>
                <li>
                  We do not use Google user data for serving advertisements,
                  including retargeting, personalized, or interest-based
                  advertising.
                </li>
                <li>
                  We do not allow humans to read Google user data unless
                  (a) we have your affirmative agreement for specific messages,
                  (b) it is necessary for security purposes such as
                  investigating abuse, (c) it is necessary to comply with
                  applicable law, or (d) the data has been aggregated and
                  anonymized for internal operations.
                </li>
                <li>
                  We do not use or transfer Google user data to determine
                  credit-worthiness or for lending purposes.
                </li>
              </ul>

              <p>
                For a per-scope justification of every Google permission we
                request, see{' '}
                <a href="/oauth-scopes#google">OAuth Scopes — Google</a>.
              </p>

              <h2 id="meta-platform">4. Meta Platform compliance</h2>
              <p>
                When you connect a Meta account (Facebook, Instagram, WhatsApp,
                or Meta Ads), we comply with the Meta Platform Terms and Meta
                Developer Policies. We:
              </p>
              <ul>
                <li>
                  Request only the scopes required for the connectors you
                  actually use. See{' '}
                  <a href="/oauth-scopes#meta">OAuth Scopes — Meta</a>.
                </li>
                <li>
                  Store Meta access tokens encrypted at rest; refresh them
                  according to Meta&rsquo;s rotation rules.
                </li>
                <li>
                  Process webhook events synchronously into your workflows; do
                  not persist webhook payloads beyond run history retention.
                </li>
                <li>
                  Honor user-initiated disconnect (Meta → Settings → Business
                  Integrations) and revoke the credential in our system on the
                  next webhook delivery.
                </li>
                <li>
                  Provide a <a href="/data-deletion">data-deletion</a> endpoint
                  for both account-level and Meta-account-only revocation.
                </li>
              </ul>

              <h2 id="sharing">5. How we share information</h2>
              <p>We share data only:</p>
              <ul>
                <li>
                  <strong>With subprocessors</strong> required to operate the
                  Service — see our{' '}
                  <a href="/transparency#subprocessors">Subprocessors list</a>.
                  Each is bound by a Data Processing Agreement.
                </li>
                <li>
                  <strong>When you direct us</strong> — every connected-app
                  call is the consequence of a workflow you built. We do not
                  initiate third-party API calls except as your workflow
                  dictates.
                </li>
                <li>
                  <strong>For legal compliance</strong> — when required by law,
                  subpoena, or court order. We will notify you unless legally
                  prohibited.
                </li>
                <li>
                  <strong>In a business transfer</strong> — if we are acquired,
                  the acquirer receives your data subject to the same
                  protections; you will be notified.
                </li>
              </ul>

              <h2 id="retention">6. Data retention &amp; deletion</h2>
              <p>
                Workspace data is retained while your account is active. You
                control granular deletion from the product UI:
              </p>
              <ul>
                <li>Delete a workflow → gone immediately, no soft-delete.</li>
                <li>
                  Disconnect a credential → OAuth token revoked at the provider
                  where supported, credential row deleted from our DB
                  immediately.
                </li>
                <li>
                  Delete a workspace → all runs, workflows, knowledge bases, and
                  memberships removed within minutes.
                </li>
                <li>
                  Delete your account → full purge within 30 days. See{' '}
                  <a href="/data-deletion">Data Deletion</a> for the exact
                  procedure.
                </li>
              </ul>
              <p>
                Operational logs roll off automatically after 30 days. Database
                backups (encrypted, region-pinned) retain for up to 30 days
                before rotation, after which deleted data is unrecoverable.
              </p>

              <h2 id="security">7. Security</h2>
              <ul>
                <li>All transport TLS 1.2+. HSTS preload enabled.</li>
                <li>Passwords hashed with Argon2id (memory-hard).</li>
                <li>
                  OAuth tokens + third-party API keys encrypted at rest with
                  AES-256 (Fernet) using per-tenant key derivation.
                </li>
                <li>
                  Production access restricted to SSH keys; every operator
                  action audit-logged.
                </li>
                <li>
                  Container images scanned on every build (Trivy) for CVEs;
                  CRITICAL findings block deploys.
                </li>
                <li>
                  Stripe handles all payment data; we never see card numbers.
                </li>
                <li>
                  Dependencies updated weekly (Dependabot) with auto-test
                  validation.
                </li>
              </ul>
              <p>
                Full security posture documented at{' '}
                <a href="/security">/security</a>.
              </p>

              <h2 id="your-rights">8. Your rights</h2>
              <p>
                Depending on your jurisdiction (GDPR / UK GDPR / CCPA / LGPD /
                etc.) you have some or all of the following rights:
              </p>
              <ul>
                <li>Access the personal data we hold about you.</li>
                <li>Correct inaccurate data.</li>
                <li>Delete your data (right to erasure).</li>
                <li>Export your data in a portable format.</li>
                <li>Restrict or object to certain processing.</li>
                <li>Withdraw consent at any time.</li>
                <li>
                  Lodge a complaint with your local data protection authority.
                </li>
              </ul>
              <p>
                Submit requests to{' '}
                <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>. We
                respond within 30 days.
              </p>

              <h2 id="international">9. International transfers</h2>
              <p>
                The Service is operated from infrastructure in the European
                Union and the United States. When data is transferred outside
                your jurisdiction, we rely on Standard Contractual Clauses
                (SCCs) or equivalent safeguards.
              </p>

              <h2 id="children">10. Children</h2>
              <p>
                The Service is not directed to children under 16. We do not
                knowingly collect personal information from anyone under 16. If
                you believe a child has provided us with personal data, contact{' '}
                <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a> and we
                will delete it.
              </p>

              <h2 id="changes">11. Changes to this policy</h2>
              <p>
                Material changes are announced at least 30 days in advance via
                the product UI and email to all account holders. Non-material
                clarifications are reflected by bumping the &ldquo;Last
                updated&rdquo; date at the top.
              </p>

              <h2 id="contact">12. Contact</h2>
              <p>
                Privacy / GDPR / data-subject requests:{' '}
                <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>
                <br />
                General support:{' '}
                <a href={`mailto:${SUPPORT_EMAIL}`}>{SUPPORT_EMAIL}</a>
                <br />
                Legal entity: RunMyCrew (proprietor: Bibek Timilsina) —
                registered address available on request.
              </p>
            </article>
          </Container>
        </section>
      </main>
      <MarketingFooter />
    </>
  )
}
