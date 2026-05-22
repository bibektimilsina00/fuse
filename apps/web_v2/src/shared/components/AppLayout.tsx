import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { LayoutDashboard, Settings, Layers, LogOut, Zap } from 'lucide-react'
import { useAuth } from '@/features/auth/hooks/useAuth'
import { Avatar, ThemeToggle, Breadcrumb, Button } from '@/shared/components'
import { APP_ROUTES } from '@/shared/constants/routes'

/**
 * AppLayout provides the main sidebar structure and header for authenticated views.
 */
export function AppLayout() {
  const { user, logout } = useAuth()
  const location = useLocation()

  return (
    <div className="flex h-screen w-screen bg-bg overflow-hidden relative">
      {/* Background Dot Grid */}
      <div className="dot-grid" />

      {/* Sidebar navigation */}
      <aside className="w-64 shrink-0 bg-bg2/50 backdrop-blur-md border-r border-border-faint flex flex-col z-10">
        {/* Header */}
        <div className="h-16 px-6 border-b border-border-faint flex items-center gap-3">
          <div className="w-8 h-8 rounded-[8px] bg-text text-bg flex items-center justify-center shadow-sm">
            <Zap size={16} />
          </div>
          <div>
            <span className="text-sm font-semibold tracking-tight text-text">Fuse Workspace</span>
            <p className="text-[10px] text-text-faint font-medium">V2 Operations</p>
          </div>
        </div>

        {/* Links */}
        <nav className="flex-1 px-4 py-6 flex flex-col gap-1.5">
          <NavLink
            to={APP_ROUTES.DASHBOARD}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-[8px] text-xs font-medium transition-all ${
                isActive
                  ? 'bg-accent/10 text-accent border border-accent/20'
                  : 'text-text-mute hover:bg-surface/40 hover:text-text border border-transparent'
              }`
            }
          >
            <LayoutDashboard size={14} />
            <span>Dashboard</span>
          </NavLink>

          <NavLink
            to={APP_ROUTES.SHOWCASE}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-[8px] text-xs font-medium transition-all ${
                isActive
                  ? 'bg-accent/10 text-accent border border-accent/20'
                  : 'text-text-mute hover:bg-surface/40 hover:text-text border border-transparent'
              }`
            }
          >
            <Layers size={14} />
            <span>Component Showcase</span>
          </NavLink>

          <NavLink
            to={APP_ROUTES.SETTINGS}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-[8px] text-xs font-medium transition-all ${
                isActive
                  ? 'bg-accent/10 text-accent border border-accent/20'
                  : 'text-text-mute hover:bg-surface/40 hover:text-text border border-transparent'
              }`
            }
          >
            <Settings size={14} />
            <span>Settings</span>
          </NavLink>
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-border-faint flex flex-col gap-4">
          <div className="flex items-center justify-between px-2">
            <span className="text-xs text-text-faint font-medium">Appearance</span>
            <ThemeToggle />
          </div>

          <div className="p-2.5 bg-bg/50 border border-border-faint rounded-[10px] flex items-center justify-between gap-3">
            <div className="flex items-center gap-2.5 overflow-hidden">
              <Avatar
                src={user?.avatar_url || undefined}
                fallback={user?.full_name || user?.email || '?'}
                size="sm"
                className="bg-accent/10 text-accent border border-border-faint"
              />
              <div className="flex flex-col min-w-0">
                <span className="text-xs font-semibold text-text truncate">
                  {user?.full_name || 'Anonymous User'}
                </span>
                <span className="text-[10px] text-text-faint truncate">
                  {user?.email}
                </span>
              </div>
            </div>

            <Button
              variant="icon-sm"
              onClick={logout}
              leftIcon={<LogOut size={14} />}
              className="border-transparent hover:border-transparent hover:bg-surface/80 text-text-faint hover:text-err"
              title="Logout"
            />
          </div>
        </div>
      </aside>

      {/* Main Page Area */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden z-10 bg-bg/20">
        <header className="h-16 px-8 border-b border-border-faint flex items-center justify-between bg-bg2/25 backdrop-blur-sm animate-fade-in">
          <Breadcrumb
            items={[
              { label: 'Workspace' },
              { label: location.pathname.substring(1) || 'dashboard' },
            ]}
          />
        </header>

        <div className="flex-1 overflow-y-auto p-8 relative">
          <Outlet />
        </div>
      </main>
    </div>
  )
}

