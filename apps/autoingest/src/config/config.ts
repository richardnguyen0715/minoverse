// AutoIngest Configuration
// Manages environment variables and runtime settings

import * as z from "zod"
import * as fs from "fs"
import * as path from "path"
import * as dotenv from "dotenv"

dotenv.config({ path: path.resolve(process.cwd(), ".env") })
dotenv.config({ path: path.resolve(process.cwd(), "../../.env") })

const ConfigSchema = z.object({
  // Minoverse API
  MINOVERSE_API_URL: z.string().url().default("http://localhost:8000"),
  MINOVERSE_API_KEY: z.string().optional(),

  // LLM Providers
  OPENAI_API_KEY: z.string().optional(),
  ANTHROPIC_API_KEY: z.string().optional(),
  OLLAMA_BASE_URL: z.string().url().default("http://localhost:11434"),

  // Default model
  DEFAULT_PROVIDER: z.enum(["openai", "anthropic", "ollama"]).default("ollama"),
  DEFAULT_MODEL: z.string().default("llama3.2"),

  // Ingest settings
  INGEST_TIMEOUT_MS: z.coerce.number().default(30000),
  INGEST_MAX_RETRIES: z.coerce.number().default(3),
  INGEST_RATE_LIMIT_DELAY_MS: z.coerce.number().default(1000),

  // Scraping
  PLAYWRIGHT_TIMEOUT_MS: z.coerce.number().default(15000),
  SCRAPE_USER_AGENT: z
    .string()
    .default("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"),

  // Queue (Redis/NATS)
  REDIS_URL: z.string().default("redis://localhost:6379/0"),
  NATS_URL: z.string().default("nats://localhost:4222"),
  USE_NATS: z.coerce.boolean().default(false),

  // Output
  LOG_LEVEL: z.enum(["debug", "info", "warn", "error"]).default("info"),
  OUTPUT_FORMAT: z.enum(["pretty", "json", "markdown"]).default("pretty"),
})

export type Config = z.infer<typeof ConfigSchema>

let _config: Config | null = null

export function getConfig(): Config {
  if (_config) return _config
  const result = ConfigSchema.safeParse(process.env)
  if (!result.success) {
    console.error("Configuration error:", result.error.format())
    process.exit(1)
  }
  _config = result.data
  return _config
}

export const config = new Proxy({} as Config, {
  get(_, key: string) {
    return getConfig()[key as keyof Config]
  },
})
