import { useState } from 'react'
import {
  Key, User as UserIcon, Copy, Trash2, Plus, CheckCircle2,
  Mail, Calendar, Shield
} from 'lucide-react'
import { useAuth } from '@/features/auth/hooks/useAuth'
import {
  Card, Button, Input, FormField, Divider, Avatar, Badge,
  useToast
} from '@/shared/components'

interface ApiKey {
  id: string
  name: string
  token: string
  createdAt: string
}

const mockApiKeys: ApiKey[] = [
  { id: 'key-1', name: 'Production Daemon Client', token: 'fuse_live_abc123xyz789...', createdAt: 'May 10, 2026' },
  { id: 'key-2', name: 'Staging CLI Client', token: 'fuse_test_def456uvw012...', createdAt: 'May 18, 2026' },
]

/**
 * Settings page managing user profile details and API tokens.
 */
export function Settings() {
  const { user } = useAuth()
  const { toast } = useToast()
  
  const [fullName, setFullName] = useState(user?.full_name || '')
  const [email] = useState(user?.email || '')
  const [keys, setKeys] = useState<ApiKey[]>(mockApiKeys)
  const [newKeyName, setNewKeyName] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)

  const handleSaveProfile = () => {
    toast('Profile updated', {
      variant: 'ok',
      description: 'Your details were successfully saved.',
    })
  }

  const handleCopyKey = (token: string) => {
    navigator.clipboard.writeText(token)
    toast('API Token copied', {
      variant: 'ok',
      description: 'Token copied to your system clipboard.',
    })
  }

  const handleCreateKey = () => {
    if (!newKeyName.trim()) {
      toast('Name required', {
        variant: 'err',
        description: 'Please enter a name for the new API key.',
      })
      return
    }

    setIsGenerating(true)
    setTimeout(() => {
      const newKey: ApiKey = {
        id: `key-${Date.now()}`,
        name: newKeyName,
        token: `fuse_live_${Math.random().toString(36).substring(2, 10)}${Math.random().toString(36).substring(2, 10)}...`,
        createdAt: new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
      }
      setKeys([...keys, newKey])
      setNewKeyName('')
      setIsGenerating(false)
      toast('API Key generated', {
        variant: 'ok',
        description: 'Ensure you copy the secret key now; you won\'t see it again.',
      })
    }, 600)
  }

  const handleRevokeKey = (id: string, name: string) => {
    setKeys(keys.filter((k) => k.id !== id))
    toast('API Key revoked', {
      variant: 'ok',
      description: `Revoked: ${name}`,
    })
  }

  return (
    <div className="flex flex-col gap-6 max-w-4xl">
      {/* Profile Section */}
      <Card padding="lg" className="flex flex-col gap-4">
        <div className="flex flex-col gap-1 pb-3 border-b border-border-faint">
          <h3 className="text-sm font-semibold text-text tracking-tight flex items-center gap-2">
            <UserIcon size={14} className="text-accent" />
            <span>Profile Information</span>
          </h3>
          <p className="text-xs text-text-faint">Update your identity and contact parameters.</p>
        </div>

        <div className="flex flex-col md:flex-row md:items-center gap-6 py-2">
          <Avatar
            src={user?.avatar_url || undefined}
            fallback={user?.full_name || user?.email || '?'}
            size="lg"
            className="w-16 h-16 bg-accent/15 text-accent border border-border-faint text-lg"
          />
          <div className="flex flex-col gap-1.5">
            <span className="text-xs font-semibold text-text">Workspace Account</span>
            <div className="flex flex-wrap gap-2">
              <Badge variant="accent" className="flex items-center gap-1 text-[10px]">
                <Shield size={10} /> Active Session
              </Badge>
              <Badge variant="ok" className="flex items-center gap-1 text-[10px]">
                <Calendar size={10} /> Created: {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
              </Badge>
            </div>
          </div>
        </div>

        <Divider />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <FormField label="Full Name">
            <Input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="John Doe"
              leftIcon={<UserIcon />}
            />
          </FormField>

          <FormField label="Email Address">
            <Input
              type="email"
              value={email}
              disabled
              placeholder="name@company.com"
              leftIcon={<Mail />}
            />
          </FormField>
        </div>

        <div className="flex justify-end pt-2">
          <Button variant="primary" onClick={handleSaveProfile}>
            <CheckCircle2 size={12} className="mr-1.5" />
            Save Profile
          </Button>
        </div>
      </Card>

      {/* API Keys Section */}
      <Card padding="lg" className="flex flex-col gap-4">
        <div className="flex flex-col gap-1 pb-3 border-b border-border-faint">
          <h3 className="text-sm font-semibold text-text tracking-tight flex items-center gap-2">
            <Key size={14} className="text-accent" />
            <span>Developer Access Keys</span>
          </h3>
          <p className="text-xs text-text-faint">Authenticate command line agents and remote microservices.</p>
        </div>

        {/* Create API key form */}
        <div className="flex gap-3 bg-bg/50 p-3.5 border border-border-faint rounded-[10px]">
          <div className="flex-1">
            <Input
              placeholder="Enter new key description (e.g. Server CLI)..."
              value={newKeyName}
              onChange={(e) => setNewKeyName(e.target.value)}
              disabled={isGenerating}
            />
          </div>
          <Button variant="primary" onClick={handleCreateKey} loading={isGenerating}>
            <Plus size={12} className="mr-1.5" />
            Generate
          </Button>
        </div>

        {/* Existing API Keys list */}
        <div className="flex flex-col gap-2 mt-2">
          {keys.length === 0 ? (
            <div className="text-center py-6 text-xs text-text-faint border border-dashed border-border-faint rounded-[10px]">
              No API keys configured.
            </div>
          ) : (
            keys.map((k) => (
              <div
                key={k.id}
                className="flex items-center justify-between gap-4 p-3 bg-bg/20 border border-border-faint hover:border-border-soft rounded-[10px] transition-colors"
              >
                <div className="flex flex-col gap-1">
                  <span className="text-xs font-semibold text-text">{k.name}</span>
                  <span className="font-mono text-[10px] text-text-faint bg-bg px-2 py-0.5 rounded-[4px] border border-border-faint max-w-max select-all">
                    {k.token}
                  </span>
                  <span className="text-[9px] text-text-dim mt-0.5">Created on {k.createdAt}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Button
                    variant="secondary"
                    size="sm"
                    className="h-8 w-8 p-0 justify-center"
                    onClick={() => handleCopyKey(k.token)}
                    title="Copy API Token"
                  >
                    <Copy size={12} />
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    className="h-8 w-8 p-0 justify-center hover:text-err"
                    onClick={() => handleRevokeKey(k.id, k.name)}
                    title="Revoke API Key"
                  >
                    <Trash2 size={12} />
                  </Button>
                </div>
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  )
}
