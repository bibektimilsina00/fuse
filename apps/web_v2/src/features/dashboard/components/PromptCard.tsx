import React, { useState } from 'react'
import { Icons, useToast } from '@/shared/components'

interface PromptCardProps {
  onSubmit: (prompt: string, mode: 'flow' | 'agent') => void
}

export function PromptCard({ onSubmit }: PromptCardProps) {
  const { toast } = useToast()
  const [prompt, setPrompt] = useState('')
  const [mode, setMode] = useState<'flow' | 'agent'>('flow')

  const handleSend = () => {
    onSubmit(prompt, mode)
    setPrompt('')
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="prompt-card">
      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Describe an automation. fuse drafts the flow, wires the connectors, and tests it before shipping."
      />
      <div className="prompt-foot">
        <div className="prompt-tools">
          <button
            className="tool-btn"
            title="Attach"
            onClick={() => toast('Attachment feature', { description: 'File uploads will be available in the next release.' })}
          >
            <Icons.Plus className="w-3.5 h-3.5" />
          </button>
          <div className="mode-toggle">
            <button
              className={mode === 'flow' ? 'active' : ''}
              onClick={() => setMode('flow')}
            >
              <Icons.Flow className="w-3 h-3" />
              <span>Flow</span>
            </button>
            <button
              className={mode === 'agent' ? 'active' : ''}
              onClick={() => setMode('agent')}
            >
              <Icons.Spark className="w-3 h-3 text-accent" />
              <span>Agent</span>
            </button>
          </div>
        </div>
        <div className="prompt-tools">
          <button
            className="tool-btn"
            title="Connections"
            onClick={() => toast('Quick connections view', { description: 'Showing 18 active connectors.' })}
          >
            <Icons.Plug className="w-3.5 h-3.5" />
          </button>
          <div
            className="model-pill cursor-pointer"
            onClick={() => toast('Model selected', { description: 'Currently utilizing Filament 2 for generation.' })}
          >
            <span className="spark">
              <Icons.Spark style={{ width: 12, height: 12 }} />
            </span>
            <span>Filament 2</span>
            <Icons.Caret style={{ width: 11, height: 11, color: 'var(--text-mute)' }} />
          </div>
          <button
            className="tool-btn"
            title="Dictate"
            onClick={() => toast('Voice Input', { description: 'Speech-to-text is currently being trained.' })}
          >
            <Icons.Mic className="w-3.5 h-3.5" />
          </button>
          <button className="send-btn" onClick={handleSend} title="Send prompt">
            <Icons.ArrowUp className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  )
}
