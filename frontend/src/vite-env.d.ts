/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE: string
  readonly VITE_API_KEY?: string
  readonly VITE_DEFAULT_RUN_ID?: string
  readonly VITE_TOP_K?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
} 