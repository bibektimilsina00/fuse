import Editor from 'react-simple-code-editor'
import Prism from 'prismjs'
import 'prismjs/components/prism-markdown'
import { cn } from '@/lib/cn'

interface SkillContentEditorProps {
  value: string
  onChange: (next: string) => void
  placeholder?: string
  className?: string
}

/**
 * Markdown body editor for a skill.
 *
 * react-simple-code-editor wraps a contenteditable-style textarea with
 * Prism syntax highlighting. ~30KB total (vs ~3MB for Monaco) and the
 * same package CodeRenderer already uses. The Prism markdown grammar
 * covers headings, lists, fenced code, links, bold/italic, blockquotes —
 * everything a skill body actually needs.
 */
export function SkillContentEditor({ value, onChange, placeholder, className }: SkillContentEditorProps) {
  return (
    <div
      className={cn(
        'flex-1 overflow-auto rounded-[8px] border border-border-faint bg-bg',
        'focus-within:border-border focus-within:bg-surface',
        'transition-[background-color,border-color] duration-[120ms]',
        className,
      )}
    >
      <Editor
        value={value}
        onValueChange={onChange}
        highlight={code => Prism.highlight(code, Prism.languages.markdown, 'markdown')}
        padding={16}
        placeholder={placeholder}
        textareaClassName="outline-none"
        preClassName="font-mono"
        style={{
          fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
          fontSize: 13,
          lineHeight: 1.6,
          minHeight: '100%',
        }}
      />
    </div>
  )
}
