'use client'

const AGENT_STEPS = [
  { label: 'Analyzing query…', delay: 0 },
  { label: 'Retrieving relevant sources…', delay: 800 },
  { label: 'Synthesizing answer…', delay: 1600 },
]

export function AgentActivity() {
  return (
    <div className="flex justify-start">
      <div className="flex flex-col gap-1.5 max-w-[85%]">
        <span className="text-[11px] font-semibold text-primary">⬡ minoverse</span>
        <div className="rounded-2xl rounded-tl-sm border border-primary/20 bg-card/60 px-4 py-3 flex flex-col gap-2">
          {AGENT_STEPS.map((step) => (
            <AgentStep key={step.label} label={step.label} />
          ))}
        </div>
      </div>
    </div>
  )
}

function AgentStep({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="inline-block w-3 h-3 rounded-full border-2 border-primary border-t-transparent animate-spin shrink-0" />
      <span className="text-xs text-muted-foreground">{label}</span>
    </div>
  )
}
