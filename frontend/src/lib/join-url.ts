/**
 * Join a base URL and a path without double slashes.
 *
 * joinApiUrl("https://api.example.com/api/v1", "/users/") → "https://api.example.com/api/v1/users/"
 * joinApiUrl("https://api.example.com/api/v1/", "/users/") → "https://api.example.com/api/v1/users/"
 */
export function joinApiUrl(base: string, path: string): string {
  return base.replace(/\/+$/, "") + "/" + path.replace(/^\/+/, "");
}
