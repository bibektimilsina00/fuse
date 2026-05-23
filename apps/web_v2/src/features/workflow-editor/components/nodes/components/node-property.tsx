import { Handle, Position } from 'reactflow'
import { cn } from '@/lib/cn'

interface NodePropertyProps {
  label: string
  value: string
  handleId?: string
  handleClass?: string
  labelClass?: string
  direction?: 'vertical' | 'horizontal'
  index?: number
  total?: number
}

const BASE_HANDLE = 'react-flow__handle nodrag nopan !z-[50] !cursor-crosshair !border-none !transition-all !duration-150 !bg-[var(--border)]'
const H_OUT = cn(BASE_HANDLE, '!h-[14px] !w-[5px] !right-[-6px] !rounded-r-[2px] !rounded-l-none hover:!right-[-8px] hover:!rounded-r-full hover:!w-[7px]')
const V_OUT = cn(BASE_HANDLE, '!w-[14px] !h-[5px] !bottom-[-6px] !rounded-b-[2px] !rounded-t-none hover:!bottom-[-8px] hover:!rounded-b-full hover:!h-[7px]')

export const NodeProperty = ({
  label,
  value,
  handleId,
  handleClass,
  labelClass,
  direction = 'horizontal',
  index = 0,
  total = 1,
}: NodePropertyProps) => {
  const isV = direction === 'vertical'

  const handleStyle: React.CSSProperties = isV
    ? { left: `${((index + 1) * 100) / (total + 1)}%` }
    : { top: '50%' }

  return (
    <div className="relative flex h-[17px] items-center gap-1.5 px-2.5 font-[var(--font-ui)]">
      <span
        className={cn('min-w-0 truncate text-[10px] font-medium capitalize leading-none text-[var(--text-faint)]', labelClass)}
        title={label}
      >
        {label}
      </span>
      <span
        className="flex-1 truncate text-right text-[10px] font-medium leading-none text-[var(--text-mute)]"
        title={value}
      >
        {value}
      </span>

      {handleId && (
        <Handle
          key={`${handleId}-${direction}`}
          type="source"
          position={isV ? Position.Bottom : Position.Right}
          id={handleId}
          className={cn(isV ? V_OUT : H_OUT, handleClass)}
          style={handleStyle}
        />
      )}
    </div>
  )
}
