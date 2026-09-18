/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Full origin of a separately-hosted backend (e.g. a Railway URL).
   * Leave unset for same-origin deployments (local dev proxy, Docker/nginx). */
  readonly VITE_API_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
