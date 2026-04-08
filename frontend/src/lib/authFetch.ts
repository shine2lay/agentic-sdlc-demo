export async function authFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  return fetch(input, { ...init, headers: { 'Content-Type': 'application/json', ...init?.headers } });
}
