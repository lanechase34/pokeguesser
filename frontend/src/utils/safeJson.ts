/**
 * Handle malformed JSON packets or empty 204 responses
 */
export async function safeJson<T>(response: Response): Promise<T | null> {
    try {
        return (await response.json()) as T;
    } catch {
        return null; // allow empty / invalid JSON
    }
}
