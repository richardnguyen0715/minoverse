// Tool Registry — registers all tools and exports the global registry

import { globalRegistry } from "./base"
import { ScrapeUrlTool, ExtractArticleTool, ExtractVideoTool, ExtractRepoTool } from "./scrape"
import {
  SearchWebTool,
  FindRepoTool,
  SearchHackerNewsTool,
  SearchRedditTool,
} from "./research"
import {
  ExtractEntitiesTool,
  QueryMemoryTool,
  StoreMemoryTool,
  BuildGraphTool,
  QueryGraphTool,
} from "./knowledge"
import {
  SummarizeShortTool,
  SummarizeTechnicalTool,
  SummarizeResearchTool,
} from "./summarize"

// Register all tools
globalRegistry.register(new ScrapeUrlTool())
globalRegistry.register(new ExtractArticleTool())
globalRegistry.register(new ExtractVideoTool())
globalRegistry.register(new ExtractRepoTool())
globalRegistry.register(new SearchWebTool())
globalRegistry.register(new FindRepoTool())
globalRegistry.register(new SearchHackerNewsTool())
globalRegistry.register(new SearchRedditTool())
globalRegistry.register(new ExtractEntitiesTool())
globalRegistry.register(new QueryMemoryTool())
globalRegistry.register(new StoreMemoryTool())
globalRegistry.register(new BuildGraphTool())
globalRegistry.register(new QueryGraphTool())
globalRegistry.register(new SummarizeShortTool())
globalRegistry.register(new SummarizeTechnicalTool())
globalRegistry.register(new SummarizeResearchTool())

export { globalRegistry }
export * from "./base"
export * from "./scrape"
export * from "./research"
export * from "./knowledge"
export * from "./summarize"
