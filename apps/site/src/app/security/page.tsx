import type { Metadata } from 'next'
import { MarketingNav, MarketingFooter } from '@/features/marketing'
import { Container } from '@/shared/components/Container'

export const metadata: Metadata = {
  title: 'Security',
  description:
    'How RunMyCrew protects your account, your data, and the credentials you connect — at every layer.',
}

const SECURITY_EMAIL = 'security@runmycrew.com'

export default function SecurityPage() {
  return (
    <>
      <MarketingNav />
      <main>
        <section className="pb-12 pt-[120px] sm:pt-[170px]">
          <Container className="max-w-[760px] px-7">
            <p className="m-0 text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
              Trust · Security
            </p>
            <h1 className="m-0 mt-3 text-[clamp(32px,4vw,48px)] font-[560] leading-[1.1] tracking-[-0.022em] text-foreground">
              Security
            </h1>
            <p className="mt-4 text-[14px] text-muted-foreground">
              How we protect your account, your data, and the credentials you
              connect — at every layer.
            </p>
          </Container>
        </section>

        <section className="pb-24">
          <Container className="max-w-[760px] px-7">
            <article className="prose prose-invert max-w-none text-[15px] leading-[1.7]">
              <h2 id="overview">Overview</h2>
              <p>
                RunMyCrew sits between you and the apps you trust most — your
                inbox, your CRM, your team chat. We treat that responsibility
                accordingly. This page documents how we protect data in transit,
                at rest, in process, and after deletion, plus our process for
                incident response and vulnerability disclosure.
              </p>

              <h2 id="auth">Authentication</h2>
              <ul>
                <li>
                  Passwords are hashed with{' '}
                  <strong>Argon2id</strong> (memory cost ≥ 64 MiB, time cost
                  ≥ 3). We never store plaintext passwords.
                </li>
                <li>
                  Optional Google Sign-In via OpenID Connect. We accept the
                  Google ID token, validate signature + audience + expiry +{' '}
                  <code>email_verified</code>, and create or look up a local
                  user.
                </li>
                <li>
                  JWT access tokens are HS256-signed, short-lived, and stored
                  in <code>localStorage</code> (not a third-party cookie). The
                  signing secret rotates with each deploy unless explicitly
                  pinned.
                </li>
                <li>
                  CSRF on the Google sign-in callback is defended with a
                  short-lived signed state JWT carrying a per-request nonce.
                </li>
                <li>
                  Password reset tokens are JWTs with a 15-minute TTL and a
                  dedicated <code>type</code> claim that prevents login tokens
                  from being reused as reset tokens.
                </li>
                <li>
                  Rate limits per IP on every auth endpoint
                  (<code>/login</code>, <code>/register</code>,{' '}
                  <code>/forgot-password</code>, <code>/reset-password</code>,
                  <code>/google/start</code>, <code>/google/callback</code>).
                </li>
              </ul>

              <h2 id="encryption">Encryption</h2>
              <ul>
                <li>
                  <strong>In transit.</strong> All traffic is TLS 1.2+ with
                  modern cipher suites. HSTS is preloaded
                  (<code>max-age=31536000; includeSubDomains; preload</code>).
                  Marketing site + product app + API are all HTTPS-only.
                </li>
                <li>
                  <strong>At rest (application).</strong> OAuth refresh tokens,
                  API keys, webhook secrets, and any user-supplied credential
                  are encrypted with <strong>AES-256 Fernet</strong> using a
                  per-deployment master key (<code>ENCRYPTION_KEY</code>) that
                  never leaves the secret store.
                </li>
                <li>
                  <strong>At rest (database + backups).</strong> Postgres
                  storage is encrypted at the volume level by the cloud
                  provider. Nightly dumps are gzip-compressed and stored in a
                  separate volume; rotation is 14 days.
                </li>
              </ul>

              <h2 id="data-isolation">Tenant + data isolation</h2>
              <ul>
                <li>
                  Every API request is authenticated and re-authorized against
                  the requesting user&rsquo;s workspace membership. Workspace
                  scoping is enforced at the repository layer, not just the
                  router.
                </li>
                <li>
                  Workflow execution is isolated per workspace; one
                  workspace&rsquo;s credentials are never visible from another
                  workspace.
                </li>
                <li>
                  Code-execution nodes (Python sandbox) run in a stripped
                  environment with no inherited worker env (verified by a
                  canary test: a worker env var is unreachable from sandboxed
                  user code).
                </li>
              </ul>

              <h2 id="oauth">Third-party OAuth handling</h2>
              <ul>
                <li>
                  We only request the minimal scopes required for the
                  connector you actually use. See{' '}
                  <a href="/oauth-scopes">OAuth Scopes</a> for the per-provider
                  list.
                </li>
                <li>
                  Refresh tokens are encrypted at rest and never logged.
                  Access tokens are kept in memory for the duration of a
                  request.
                </li>
                <li>
                  Webhook signature verification is mandatory and
                  cryptographically time-safe
                  (<code>hmac.compare_digest</code> equivalent).
                </li>
              </ul>

              <h2 id="infrastructure">Infrastructure</h2>
              <ul>
                <li>
                  Production runs on a hardened single-VPS Docker Compose stack
                  fronted by Caddy. SSH is key-only; password auth is disabled
                  in <code>sshd_config</code>.
                </li>
                <li>
                  Container images are built reproducibly in GitHub Actions,
                  signed with cosign attestations, and scanned by Trivy on
                  every push. <strong>CRITICAL</strong> CVEs block the deploy.
                </li>
                <li>
                  Caddy issues + renews Let&rsquo;s Encrypt certificates
                  automatically. All app responses include modern security
                  headers (HSTS, X-Content-Type-Options, X-Frame-Options,
                  Referrer-Policy, Permissions-Policy).
                </li>
                <li>
                  Operator access to production is restricted to a small
                  allow-list of SSH keys; every <code>ssh</code> session is
                  logged.
                </li>
                <li>
                  Database backups are tested for restorability monthly.
                </li>
              </ul>

              <h2 id="dev">Software development practices</h2>
              <ul>
                <li>
                  Code is reviewed before merge to <code>main</code>. CI runs
                  ruff (Python lint), tsc (TypeScript), eslint, and the test
                  suite on every PR.
                </li>
                <li>
                  Dependencies are kept current via Dependabot with daily
                  scans and grouped weekly merges.
                </li>
                <li>
                  Secret scanning runs pre-commit and on the server (Detect
                  Hardcoded Secrets).
                </li>
                <li>
                  Production deploys are automated via GitHub Actions with
                  pinned image digests for atomic rollback.
                </li>
              </ul>

              <h2 id="incident">Incident response</h2>
              <p>
                If you suspect a security issue, email{' '}
                <a href={`mailto:${SECURITY_EMAIL}`}>{SECURITY_EMAIL}</a>{' '}
                immediately. We aim to:
              </p>
              <ul>
                <li>Acknowledge within 24 hours.</li>
                <li>Triage and reproduce within 3 business days.</li>
                <li>
                  Patch and disclose to affected users within 30 days, sooner
                  if the issue is actively exploited.
                </li>
                <li>
                  Notify regulators where required (e.g. GDPR Art. 33 — 72
                  hours).
                </li>
              </ul>
              <p>
                We will credit researchers who responsibly disclose, with
                their consent, in our release notes.
              </p>

              <h2 id="disclosure">Coordinated vulnerability disclosure</h2>
              <p>
                Security researchers acting in good faith are safe-harbored
                under our Responsible Disclosure policy. Please:
              </p>
              <ul>
                <li>
                  Test only against accounts and workspaces you own. Use
                  free-tier accounts to avoid affecting other customers.
                </li>
                <li>
                  Do not access, modify, or delete data belonging to other
                  users. Stop and notify us if you encounter such data.
                </li>
                <li>
                  Do not perform DDoS, brute-force, automated scanning at
                  scale, or social engineering of staff.
                </li>
                <li>
                  Give us a reasonable window to remediate before public
                  disclosure (typically 90 days; faster for trivial issues).
                </li>
              </ul>
              <p>
                Eligible report categories include but are not limited to:
                authentication / authorization flaws, broken access control,
                injection (SQL / template), SSRF, RCE, sensitive-data leakage,
                broken OAuth handling, and significant denial-of-service
                vectors.
              </p>

              <h2 id="contact">Contact</h2>
              <p>
                Security inbox:{' '}
                <a href={`mailto:${SECURITY_EMAIL}`}>{SECURITY_EMAIL}</a>
                <br />
                PGP key: published at{' '}
                <a href="/.well-known/security.txt">/.well-known/security.txt</a>{' '}
                (coming soon)
              </p>
            </article>
          </Container>
        </section>
      </main>
      <MarketingFooter />
    </>
  )
}
