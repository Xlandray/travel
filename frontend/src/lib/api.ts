/**
 * The one place that knows how to reach the API.
 *
 * Ten files used to carry their own copy of this, and five more read
 * `process.env.NEXT_PUBLIC_API_URL` directly with no fallback at all. The
 * copies were not identical, and the difference was not cosmetic: the direct
 * readers ran on the server, where that variable holds the URL a *browser*
 * should use. Inside the container `localhost:8081` is the container itself,
 * so every server-rendered fetch was refused — published articles 404'd, the
 * article list said there were none, and the sitemap silently dropped them.
 *
 * Keeping the decision in one function is what makes that fixable once.
 */

const BROWSER_FALLBACK = "http://localhost:8081/api/v1";
const SERVER_FALLBACK = "http://api:8000/api/v1";

const TOKEN_KEY = "token";

function trimTrailingSlash(url: string): string {
  return url.replace(/\/+$/, "");
}

/**
 * Where to send requests from wherever this code is running.
 *
 * The browser and the server need different answers. In the browser the API is
 * whatever the public URL is. On the server it depends on the deployment:
 * under Docker Compose the API is another container (`api:8000`), while on
 * Vercel there is no such network and the public URL is the only way in — so
 * `INTERNAL_API_URL` wins when it is set, and the public URL is the fallback
 * rather than a hardcoded container name.
 */
export function apiBase(): string {
  if (typeof window !== "undefined") {
    return trimTrailingSlash(process.env.NEXT_PUBLIC_API_URL || BROWSER_FALLBACK);
  }
  return trimTrailingSlash(
    process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL || SERVER_FALLBACK,
  );
}

export function apiUrl(path: string): string {
  return `${apiBase()}${path.startsWith("/") ? path : `/${path}`}`;
}

/** A non-2xx response, carrying whatever the backend said was wrong. */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly detail: string,
  ) {
    super(detail);
    this.name = "ApiError";
  }

  /** True when the caller should send the customer to the login page. */
  get isUnauthorized(): boolean {
    return this.status === 401;
  }
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
}

export interface ApiRequest extends Omit<RequestInit, "body"> {
  /** Sent as JSON. Set `Content-Type` yourself if you need something else. */
  json?: unknown;
  /** Attach the stored bearer token. Requests without one still go out. */
  auth?: boolean;
  /** Appended as a query string; undefined and empty values are dropped. */
  query?: Record<string, string | number | boolean | undefined | null>;
}

async function readDetail(response: Response): Promise<string> {
  try {
    const body = await response.json();
    if (typeof body?.detail === "string") return body.detail;
    if (Array.isArray(body?.detail)) return "Gönderilen bilgiler geçersiz.";
  } catch {
    // Not JSON — an nginx error page, say. The status is all we have.
  }
  return `İstek başarısız oldu (${response.status}).`;
}

/**
 * Make a request and return the decoded body.
 *
 * Throws `ApiError` on any non-2xx, so a caller cannot forget to check
 * `res.ok` and go on to read fields off an error payload — which is what the
 * hand-rolled `fetch` calls were one missing `if` away from doing.
 */
export async function apiFetch<T>(path: string, options: ApiRequest = {}): Promise<T> {
  const { json, auth, query, headers, ...rest } = options;

  const url = new URL(apiUrl(path));
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, String(value));
    }
  }

  const token = auth ? getToken() : null;
  const response = await fetch(url.toString(), {
    ...rest,
    headers: {
      ...(json !== undefined ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
    ...(json !== undefined ? { body: JSON.stringify(json) } : {}),
  });

  if (!response.ok) {
    // The token is no good any more — whether it expired, was revoked, or
    // never existed. Keeping it around only produces the same 401 again.
    if (response.status === 401) clearToken();
    throw new ApiError(response.status, await readDetail(response));
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

/**
 * Like `apiFetch`, but returns `fallback` instead of throwing.
 *
 * For places where the page still has something to show without the data —
 * a footer whose settings did not load, a list that can be empty. Anywhere a
 * failure changes what the customer should do, catch `ApiError` instead.
 */
export async function apiFetchOr<T>(
  fallback: T,
  path: string,
  options: ApiRequest = {},
): Promise<T> {
  try {
    return await apiFetch<T>(path, options);
  } catch {
    return fallback;
  }
}
