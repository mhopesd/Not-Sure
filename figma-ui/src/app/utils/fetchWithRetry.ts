/**
 * Fetch wrapper with automatic retry on server errors and network failures.
 */
export async function fetchWithRetry(
  url: string,
  options: RequestInit = {},
  retries = 3,
  delay = 1000
): Promise<Response> {
  let lastError: Error | undefined;
  for (let i = 0; i < retries; i++) {
    try {
      const response = await fetch(url, options);
      // Don't retry on client errors (4xx) — only on server errors
      if (response.ok || response.status < 500) return response;
      lastError = new Error(`Server error: ${response.status}`);
    } catch (err) {
      lastError = err instanceof Error ? err : new Error(String(err));
    }
    await new Promise((r) => setTimeout(r, delay * (i + 1)));
  }
  throw lastError || new Error(`Request failed after ${retries} retries`);
}
