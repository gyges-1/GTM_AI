/**
 * AgentBadge — coloured pill showing the active agent name.
 */

const AGENT_COLORS: Record<string, string> = {
  demand_generation: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
  pipeline_management: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  forecasting: 'bg-green-500/20 text-green-300 border-green-500/30',
  customer_success: 'bg-orange-500/20 text-orange-300 border-orange-500/30',
  growth_intelligence: 'bg-pink-500/20 text-pink-300 border-pink-500/30',
}

const AGENT_LABELS: Record<string, string> = {
  demand_generation: 'Demand Gen',
  pipeline_management: 'Pipeline',
  forecasting: 'Forecasting',
  customer_success: 'Customer Success',
  growth_intelligence: 'Growth Intel',
}

interface Props {
  agentName: string
  size?: 'sm' | 'xs'
}

export default function AgentBadge({ agentName, size = 'sm' }: Props) {
  const colorClass = AGENT_COLORS[agentName] ?? 'bg-gray-500/20 text-gray-300 border-gray-500/30'
  const label = AGENT_LABELS[agentName] ?? agentName.replace(/_/g, ' ')
  const sizeClass = size === 'xs' ? 'text-[10px] px-1.5 py-0.5' : 'text-xs px-2 py-0.5'

  return (
    <span
      className={`inline-flex items-center rounded-full border font-medium ${colorClass} ${sizeClass}`}
    >
      {label}
    </span>
  )
}
