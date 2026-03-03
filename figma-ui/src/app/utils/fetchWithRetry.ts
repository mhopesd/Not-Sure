/**
 * Fetch wrapper with automatic retry on server errors and network failures.
 */
export async function fetchWithRetry(
  url: string,
  options: RequestInit = {},
  retries = 3,
  delay = 1000
): Promise<Response> {
  for (let i = 0; i < retries; i++) {
    try {
      const response = await fetch(url, options);
      // Don't retry on client errors (4xx) — only on server errors
      if (response.ok || response.status < 500) return response;
    } catch (err) {
      if (i === retries - 1) throw err;
    }
    await new Promise((r) => setTimeout(r, delay * (i + 1)));
  }
  return fetch(url, options);
}
