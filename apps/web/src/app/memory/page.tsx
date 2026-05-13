import { MemoryBrowser } from '@/components/memory/memory-browser'

export default function MemoryPage() {
  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">💡 Memory</h1>
        <p className="text-muted-foreground mt-1">Episodic and semantic knowledge distilled by AI</p>
      </div>
      <MemoryBrowser />
    </div>
  )
}
