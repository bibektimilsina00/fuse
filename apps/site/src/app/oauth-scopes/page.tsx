import type { Metadata } from 'next'
import { MarketingNav, MarketingFooter } from '@/features/marketing'
import { Container } from '@/shared/components/Container'

export const metadata: Metadata = {
  title: 'OAuth Scopes',
  description:
    'Every OAuth scope RunMyCrew requests, why we need it, and the user-facing feature it enables. Required for Google + Meta app review.',
}

const PRIVACY_EMAIL = 'privacy@runmycrew.com'

type Scope = {
  scope: string
  purpose: string
  features: string
  sensitive?: boolean
}

const GOOGLE_SCOPES: Scope[] = [
  {
    scope: 'openid email profile',
    purpose:
      'Sign in with Google (OpenID Connect). Verifies your email and creates / matches your RunMyCrew account.',
    features: 'Google sign-in on /login and /register.',
  },
  {
    scope: 'gmail.modify',
    purpose:
      'Read, send, label, and trash messages on your Gmail account in response to your workflows.',
    features:
      'Gmail trigger (new message matching filter), Gmail action (send / reply / label / archive). Used only inside workflows you explicitly built.',
    sensitive: true,
  },
  {
    scope: 'calendar',
    purpose: 'Read and write events in your Google Calendar.',
    features:
      'Calendar trigger (event start / new event), Calendar action (create / update / delete event).',
    sensitive: true,
  },
  {
    scope: 'drive.file',
    purpose:
      'Create and manage Drive files created by RunMyCrew or explicitly opened by the user via the Google Picker. NOT broad Drive access.',
    features:
      'Drive action (upload / list / share / rename), Drive trigger (new file in a Picker-selected folder).',
  },
  {
    scope: 'spreadsheets',
    purpose: 'Read and write Google Sheets.',
    features:
      'Sheets action (read range, append row, update cell), Sheets trigger (new row).',
    sensitive: true,
  },
  {
    scope: 'documents',
    purpose: 'Read and write Google Docs.',
    features: 'Docs action (create from template, append text, read content).',
    sensitive: true,
  },
  {
    scope: 'tasks',
    purpose: 'Read and write Google Tasks.',
    features: 'Tasks action (create / complete / list).',
  },
  {
    scope: 'forms.body forms.responses.readonly',
    purpose: 'Read Form questions and response submissions.',
    features: 'Forms trigger (new response), Forms action (read questions).',
    sensitive: true,
  },
  {
    scope: 'contacts',
    purpose: 'Read and write Google Contacts.',
    features: 'People action (create / search), People trigger (new contact).',
    sensitive: true,
  },
  {
    scope: 'youtube.force-ssl youtube.upload',
    purpose: 'Manage YouTube videos, comments, playlists, and subscriptions.',
    features:
      'YouTube action (upload, update, rate, comment, list playlist), YouTube trigger (new comment, new subscriber).',
    sensitive: true,
  },
  {
    scope: 'presentations',
    purpose: 'Read and write Google Slides.',
    features: 'Slides action (replace text, add slide, export PDF).',
    sensitive: true,
  },
  {
    scope: 'chat.messages chat.spaces.readonly',
    purpose: 'Send and read messages in Google Chat spaces you are in.',
    features: 'Chat action (post message), Chat trigger (new message).',
    sensitive: true,
  },
  {
    scope: 'analytics.readonly',
    purpose: 'Read Google Analytics reports and dimensions.',
    features: 'GA4 action (run report).',
    sensitive: true,
  },
  {
    scope: 'webmasters',
    purpose: 'Read Search Console sites, sitemaps, and search queries.',
    features: 'Search Console action (top queries / inspect URL / submit sitemap).',
    sensitive: true,
  },
  {
    scope: 'devstorage.read_write',
    purpose: 'Read and write Google Cloud Storage buckets and objects.',
    features: 'GCS action (upload / list / read / copy / delete object).',
    sensitive: true,
  },
]

const META_SCOPES: Scope[] = [
  {
    scope: 'instagram_basic',
    purpose: 'Read your Instagram account name and ID.',
    features: 'Used to display the connected IG account in RunMyCrew settings.',
  },
  {
    scope: 'instagram_content_publish',
    purpose: 'Publish photos, videos, and stories to your Instagram account.',
    features: 'Instagram action (publish post / story).',
    sensitive: true,
  },
  {
    scope: 'instagram_manage_messages',
    purpose: 'Read and reply to Instagram DMs received by your business account.',
    features:
      'Instagram trigger (new DM), Instagram action (reply DM). Only within the 24-hour customer-service window per Meta policy.',
    sensitive: true,
  },
  {
    scope: 'instagram_manage_comments',
    purpose: 'Read and reply to comments on your Instagram posts.',
    features: 'Instagram trigger (new comment), Instagram action (reply comment).',
    sensitive: true,
  },
  {
    scope: 'pages_show_list pages_read_engagement pages_manage_metadata',
    purpose:
      'Discover the Facebook Pages you manage and read engagement metrics.',
    features: 'Used to select which Page to connect; metric panels in the editor.',
  },
  {
    scope: 'pages_messaging',
    purpose: 'Send and receive messages on the Page&rsquo;s Messenger inbox.',
    features:
      'Messenger trigger (new message), Messenger action (reply). 24-hour window applies.',
    sensitive: true,
  },
  {
    scope: 'pages_read_user_content pages_manage_engagement',
    purpose: 'Read and reply to comments on your Page posts.',
    features:
      'Facebook trigger (new comment on Page post), Facebook action (reply / hide comment).',
    sensitive: true,
  },
  {
    scope: 'leads_retrieval',
    purpose: 'Read lead-ad form submissions for your Page.',
    features: 'Meta Lead Ads trigger (new lead), action (fetch lead details).',
    sensitive: true,
  },
  {
    scope: 'ads_management ads_read business_management',
    purpose:
      'Read and edit your ad accounts, campaigns, ad sets, and ads (only when an Ads workflow exists).',
    features:
      'Meta Ads action (create campaign, pause ad, update budget), trigger (campaign-delivery anomaly).',
    sensitive: true,
  },
  {
    scope: 'whatsapp_business_messaging whatsapp_business_management',
    purpose:
      'Send and receive WhatsApp Business messages via the official Cloud API.',
    features:
      'WhatsApp trigger (incoming message), action (send template message, send text).',
    sensitive: true,
  },
]

const SLACK_SCOPES: Scope[] = [
  {
    scope: 'channels:read channels:history chat:write',
    purpose: 'Read channel listings + messages and post new messages on your behalf.',
    features: 'Slack trigger (new message), action (send / update message).',
  },
  {
    scope: 'users:read',
    purpose: 'Resolve user IDs to display names + avatars in the editor.',
    features: 'User picker in Slack node fields.',
  },
  {
    scope: 'reactions:write',
    purpose: 'Add / remove emoji reactions on messages.',
    features: 'Slack action (add reaction).',
  },
]

const GITHUB_SCOPES: Scope[] = [
  {
    scope: 'repo',
    purpose:
      'Read and write repository issues, PRs, releases, deployments, and code if requested by the workflow.',
    features:
      'GitHub trigger (new issue / new PR / push), action (create issue, add comment, merge PR).',
    sensitive: true,
  },
  {
    scope: 'workflow',
    purpose: 'Dispatch GitHub Actions workflows.',
    features: 'GitHub action (workflow dispatch).',
  },
]

const NOTION_SCOPES: Scope[] = [
  {
    scope: 'workspace.read workspace.write',
    purpose:
      'Read and write the databases and pages you authorized when creating the integration.',
    features: 'Notion trigger (new row), action (create page / append block).',
  },
]

const SCOPE_GROUPS = [
  { id: 'google',  title: 'Google',  scopes: GOOGLE_SCOPES },
  { id: 'meta',    title: 'Meta (Facebook · Instagram · WhatsApp · Ads)', scopes: META_SCOPES },
  { id: 'slack',   title: 'Slack',   scopes: SLACK_SCOPES },
  { id: 'github',  title: 'GitHub',  scopes: GITHUB_SCOPES },
  { id: 'notion',  title: 'Notion',  scopes: NOTION_SCOPES },
]

export default function OauthScopesPage() {
  return (
    <>
      <MarketingNav />
      <main>
        <section className="pb-12 pt-[120px] sm:pt-[170px]">
          <Container className="max-w-[860px] px-7">
            <p className="m-0 text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground/70">
              Developers · OAuth Scopes
            </p>
            <h1 className="m-0 mt-3 text-[clamp(32px,4vw,48px)] font-[560] leading-[1.1] tracking-[-0.022em] text-foreground">
              OAuth Scopes
            </h1>
            <p className="mt-4 text-[15px] text-muted-foreground">
              Every OAuth permission RunMyCrew requests, why we need it, and
              the user-facing feature it enables. Sensitive / restricted scopes
              are flagged. Scopes are requested only when you connect a
              specific integration — connecting Slack does not request Google
              scopes, etc.
            </p>
          </Container>
        </section>

        <section className="pb-24">
          <Container className="max-w-[860px] px-7">
            <article className="prose prose-invert max-w-none text-[15px] leading-[1.7]">
              <p>
                For our broader privacy commitments — including the Google API
                Services User Data Policy <strong>Limited Use</strong> disclosure
                and Meta Platform compliance — see the{' '}
                <a href="/privacy">Privacy Policy</a>.
              </p>

              {SCOPE_GROUPS.map((group) => (
                <section key={group.id} id={group.id} className="mt-12">
                  <h2 className="mt-0">{group.title}</h2>
                  <table>
                    <thead>
                      <tr>
                        <th style={{ width: '28%' }}>Scope</th>
                        <th style={{ width: '38%' }}>Why we request it</th>
                        <th>User-facing feature</th>
                      </tr>
                    </thead>
                    <tbody>
                      {group.scopes.map((s) => (
                        <tr key={s.scope}>
                          <td>
                            <code style={{ whiteSpace: 'normal' }}>
                              {s.scope}
                            </code>
                            {s.sensitive ? (
                              <>
                                <br />
                                <span
                                  style={{
                                    fontSize: '11px',
                                    color: 'var(--accent)',
                                    fontWeight: 600,
                                    textTransform: 'uppercase',
                                    letterSpacing: '0.06em',
                                  }}
                                >
                                  Sensitive
                                </span>
                              </>
                            ) : null}
                          </td>
                          <td>{s.purpose}</td>
                          <td>{s.features}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </section>
              ))}

              <h2 className="mt-16">Questions?</h2>
              <p>
                If you&rsquo;re a reviewer or a privacy-conscious user and need
                clarification on any scope, email{' '}
                <a href={`mailto:${PRIVACY_EMAIL}`}>{PRIVACY_EMAIL}</a>. We
                respond within 2 business days.
              </p>
            </article>
          </Container>
        </section>
      </main>
      <MarketingFooter />
    </>
  )
}
