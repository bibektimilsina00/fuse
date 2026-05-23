import { Handle, Position } from 'reactflow'
import type { NodeDefinition } from '../../../types/editorTypes'
import { cn } from '@/lib/cn'

interface NodeHandlesProps {
  definition: NodeDefinition
  omitOutputs?: boolean
  direction?: 'vertical' | 'horizontal'
}

const BASE = 'react-flow__handle nodrag nopan !z-[50] !cursor-crosshair !border-none !transition-all !duration-150 !bg-[var(--border)]'

const H_IN = cn(BASE, '!h-[14px] !w-[5px] !left-[-6px] !rounded-l-[2px] !rounded-r-none hover:!left-[-8px] hover:!rounded-l-full hover:!w-[7px]')
const H_OUT = cn(BASE, '!h-[14px] !w-[5px] !right-[-6px] !rounded-r-[2px] !rounded-l-none hover:!right-[-8px] hover:!rounded-r-full hover:!w-[7px]')
const V_IN = cn(BASE, '!w-[14px] !h-[5px] !top-[-6px] !rounded-t-[2px] !rounded-b-none hover:!top-[-8px] hover:!rounded-t-full hover:!h-[7px]')
const V_OUT = cn(BASE, '!w-[14px] !h-[5px] !bottom-[-6px] !rounded-b-[2px] !rounded-t-none hover:!bottom-[-8px] hover:!rounded-b-full hover:!h-[7px]')

export const NodeHandles = ({ definition, omitOutputs, direction = 'horizontal' }: NodeHandlesProps) => {
  const isV = direction === 'vertical'
  const inCount = definition.inputs ?? 0
  const outCount = definition.outputs ?? 0

  const inStyle = (i: number): React.CSSProperties =>
    isV
      ? { left: inCount === 1 ? '50%' : `${(i + 1) * (100 / (inCount + 1))}%`, transform: 'translateX(-50%)' }
      : { top: inCount === 1 ? '12px' : `${12 + i * 20}px`, transform: 'translateY(-50%)' }

  const outStyle = (i: number): React.CSSProperties =>
    isV
      ? { left: outCount === 1 ? '50%' : `${(i + 1) * (100 / (outCount + 1))}%`, transform: 'translateX(-50%)' }
      : { top: outCount === 1 ? '12px' : `${12 + i * 20}px`, transform: 'translateY(-50%)' }

  return (
    <>
      {Array.from({ length: inCount }).map((_, i) => (
        <Handle
          key={`in-${i}-${direction}`}
          type="target"
          position={isV ? Position.Top : Position.Left}
          id={`input-${i}`}
          className={isV ? V_IN : H_IN}
          style={inStyle(i)}
        />
      ))}

      {!omitOutputs && Array.from({ length: outCount }).map((_, i) => (
        <Handle
          key={`out-${i}-${direction}`}
          type="source"
          position={isV ? Position.Bottom : Position.Right}
          id={`output-${i}`}
          className={isV ? V_OUT : H_OUT}
          style={outStyle(i)}
        />
      ))}
    </>
  )
}
