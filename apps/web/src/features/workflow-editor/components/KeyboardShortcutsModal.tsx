import React from 'react'
import { Modal } from '@/components/ui/modal'

interface KeyboardShortcutsModalProps {
  open: boolean
  onClose: () => void
}

const SHORTCUT_GROUPS = [
  {
    group: 'Canvas',
    items: [
      { keys: ['⌘', 'Z'], label: 'Undo' },
      { keys: ['⌘', '⇧', 'Z'], label: 'Redo' },
      { keys: ['⌘', 'K'], label: 'Add Node (search)' },
      { keys: ['⇧', 'L'], label: 'Auto-layout' },
      { keys: ['⌘', 'Scroll'], label: 'Zoom in / out' },
      { keys: ['Space', 'Drag'], label: 'Pan canvas' },
      { keys: ['⌘', 'A'], label: 'Select all nodes' },
      { keys: ['Del'], label: 'Delete selected' },
    ],
  },
  {
    group: 'Node',
    items: [
      { keys: ['⌘', 'D'], label: 'Duplicate node' },
      { keys: ['⌘', 'L'], label: 'Lock / unlock node' },
      { keys: ['⌘', 'P'], label: 'Pin / unpin node' },
      { keys: ['F2'], label: 'Rename node' },
      { keys: ['⌘', 'Enter'], label: 'Run node test' },
    ],
  },
  {
    group: 'Workflow',
    items: [
      { keys: ['⌘', 'S'], label: 'Save workflow' },
      { keys: ['⌘', '⇧', 'P'], label: 'Run workflow' },
      { keys: ['⌘', 'L'], label: 'Open logs' },
      { keys: ['?'], label: 'Show this help' },
      { keys: ['Esc'], label: 'Close panel / menu' },
    ],
  },
]

function Kbd({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center justify-center min-w-[26px] h-[22px] px-1.5 rounded border border-[#3a3a3a] bg-[#2a2a2a] text-[11px] font-mono text-[#aaa] leading-none">
      {children}
    </span>
  )
}

export const KeyboardShortcutsModal: React.FC<KeyboardShortcutsModalProps> = ({ open, onClose }) => {
  return (
    <Modal isOpen={open} onClose={onClose} maxWidth="xl">
      <Modal.Header title="Keyboard Shortcuts" />
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 pt-2">
        {SHORTCUT_GROUPS.map(group => (
          <div key={group.group}>
            <p className="text-[11px] font-semibold uppercase tracking-wider text-[#555] mb-3">{group.group}</p>
            <div className="space-y-2">
              {group.items.map(item => (
                <div key={item.label} className="flex items-center justify-between gap-2">
                  <span className="text-[13px] text-[#ccc]">{item.label}</span>
                  <div className="flex items-center gap-0.5 flex-shrink-0">
                    {item.keys.map((k, i) => (
                      <React.Fragment key={i}>
                        {i > 0 && <span className="text-[10px] text-[#444] mx-0.5">+</span>}
                        <Kbd>{k}</Kbd>
                      </React.Fragment>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </Modal>
  )
}
