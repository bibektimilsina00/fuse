import { NavLink } from 'react-router-dom'
import { cn } from '@/lib/cn'
import { Icons } from '@/shared/components/icons'
import { APP_ROUTES } from '@/shared/constants/routes'
import { ThemeToggle } from '@/shared/components'
import type { AppLayoutController } from './use-app-layout-controller'
import { MENU_ITEM_CLASS } from './navigation'

interface AppTopBarActionsProps {
  controller: AppLayoutController
}

export function AppTopBarActions({ controller }: AppTopBarActionsProps) {
  const {
    user,
    logout,
    theme,
    setTheme,
    profileOpen,
    setProfileOpen,
    setShortcutsOpen,
    setFeedbackOpen,
  } = controller

  const userInitial = (user?.full_name || user?.email || '?').slice(0, 1).toUpperCase()

  return (
    <div className="flex items-center gap-[6px]">
      <button className="w-[32px] h-[32px] inline-flex items-center justify-center rounded-md text-[var(--text-mute)] relative transition-colors duration-120 hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[16px] [&_svg]:h-[16px]" title="Activity"><Icons.Activity /></button>
      <button className="w-[32px] h-[32px] inline-flex items-center justify-center rounded-md text-[var(--text-mute)] relative transition-colors duration-120 hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[16px] [&_svg]:h-[16px]" title="Keyboard shortcuts" onClick={() => setShortcutsOpen(true)}><Icons.Cmd /></button>
      <ThemeToggle />

      <div className="relative">
        <button
          className={cn(
            'w-[28px] h-[28px] rounded-md bg-[var(--surface-3)] border border-[var(--border-soft)] cursor-pointer inline-flex items-center justify-center text-[11px] font-semibold text-[var(--text)] tracking-tight bg-cover bg-center transition-colors duration-120 hover:border-[var(--border)]',
            profileOpen && 'bg-[var(--surface-2)] text-[var(--text)]'
          )}
          onClick={() => setProfileOpen(value => !value)}
          aria-label="Account"
          style={{ backgroundImage: user?.avatar_url ? `url(${user.avatar_url})` : undefined }}
        >
          {!user?.avatar_url && userInitial}
        </button>

        {profileOpen && (
          <>
            <div className="fixed inset-0 z-40" onClick={() => setProfileOpen(false)} />
            <div className="absolute top-[calc(100%+8px)] right-0 w-[260px] bg-[var(--bg-2)] border border-[var(--border)] rounded-lg p-[6px] shadow-[0_24px_56px_-20px_oklch(0_0_0/0.7)] z-50 animate-in fade-in slide-in-from-top-2">
              <div className="flex items-center gap-[10px] pt-[8px] px-[8px] pb-[10px]">
                <span className="w-[32px] h-[32px] rounded-md bg-[var(--surface-3)] border border-[var(--border-soft)] inline-flex items-center justify-center text-[13px] font-semibold text-[var(--text)] shrink-0">
                  {userInitial}
                </span>
                <span className="flex flex-col gap-[1px] min-w-0">
                  <span className="text-[13px] font-medium">{user?.full_name || 'Anonymous'}</span>
                  <span className="text-[11px] text-[var(--text-faint)] font-mono">{user?.email}</span>
                </span>
              </div>

              <NavLink to={APP_ROUTES.SETTINGS} className={MENU_ITEM_CLASS} onClick={() => setProfileOpen(false)}>
                <Icons.Settings /> Account settings <span className="kbd">⌘,</span>
              </NavLink>
              <NavLink to={APP_ROUTES.WORKSPACE_SETTINGS} className={MENU_ITEM_CLASS} onClick={() => setProfileOpen(false)}>
                <Icons.Settings /> Workspace settings
              </NavLink>
              <NavLink to={APP_ROUTES.CONNECTIONS} className={MENU_ITEM_CLASS} onClick={() => setProfileOpen(false)}>
                <Icons.Plug /> Connected apps
              </NavLink>
              <NavLink to={APP_ROUTES.RUNS} className={MENU_ITEM_CLASS} onClick={() => setProfileOpen(false)}>
                <Icons.Activity /> Run usage
              </NavLink>
              <div className="h-[1px] bg-[var(--border-faint)] my-[4px]" />
              <div className="px-[10px] py-[6px] flex flex-col gap-[6px] border-b border-[var(--border-faint)]">
                <span className="text-[10px] font-mono text-[var(--text-dim)] tracking-widest uppercase font-semibold">Themes</span>
                <div className="flex flex-col gap-[2px]">
                  {([
                    { id: 'midnight-dark', label: 'Midnight Dark', bg: 'bg-[oklch(0.125_0.015_240)]', accent: 'bg-[oklch(0.85_0.17_165)]' },
                    { id: 'slate-blue', label: 'Slate Blue', bg: 'bg-[oklch(0.14_0.02_260)]', accent: 'bg-[oklch(0.78_0.16_230)]' },
                    { id: 'cyber-orange', label: 'Cyber Orange', bg: 'bg-[oklch(0.11_0.006_80)]', accent: 'bg-[oklch(0.82_0.18_80)]' },
                    { id: 'light-mint', label: 'Light Mint', bg: 'bg-[oklch(0.995_0.002_165)]', accent: 'bg-[oklch(0.55_0.13_165)]' },
                    { id: 'light-slate', label: 'Light Slate', bg: 'bg-[oklch(0.99_0.002_240)]', accent: 'bg-[oklch(0.56_0.18_240)]' },
                  ] as const).map(item => (
                    <button
                      key={item.id}
                      onClick={() => setTheme(item.id)}
                      className={cn(
                        "flex items-center gap-[8px] w-full px-[8px] py-[5px] rounded-md text-[12.5px] transition-colors hover:bg-[var(--surface)]",
                        theme === item.id ? "text-[var(--text)] font-semibold bg-[var(--surface-2)]" : "text-[var(--text-mute)]"
                      )}
                    >
                      <span className={cn("w-[14px] h-[14px] rounded-full border border-[var(--border)] flex items-center justify-center shrink-0", item.bg)}>
                        <span className={cn("w-[6px] h-[6px] rounded-full", item.accent)} />
                      </span>
                      <span>{item.label}</span>
                      {theme === item.id && <Icons.Check style={{ width: 12, height: 12, color: 'var(--accent)' }} className="ml-auto shrink-0" />}
                    </button>
                  ))}
                </div>
              </div>
              <button className={MENU_ITEM_CLASS} onClick={() => { setProfileOpen(false); setShortcutsOpen(true) }}>
                <Icons.Cmd /> Keyboard shortcuts <span className="ml-auto kbd">?</span>
              </button>
              <button className={MENU_ITEM_CLASS} onClick={() => { setProfileOpen(false); window.open('https://docs.fuse.io', '_blank', 'noopener') }}>
                <Icons.Doc /> Documentation
              </button>
              <button className={MENU_ITEM_CLASS} onClick={() => { setProfileOpen(false); setFeedbackOpen(true) }}>
                <Icons.Feedback /> Send feedback
              </button>
              <div className="h-[1px] bg-[var(--border-faint)] my-[4px]" />
              <button className={cn(MENU_ITEM_CLASS, 'text-[var(--err)] hover:bg-[oklch(0.70_0.18_22/0.10)]')} onClick={() => { setProfileOpen(false); logout() }}>
                <Icons.SignOut /> Sign out
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
