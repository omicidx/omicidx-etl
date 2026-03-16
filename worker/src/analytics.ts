import type { Env } from "./index";

/**
 * Hash the first portion of a client IP for privacy-preserving analytics.
 * Returns the first 8 hex characters of the SHA-256 hash.
 */
async function hashIp(ip: string): Promise<string> {
  const data = new TextEncoder().encode(ip);
  const hash = await crypto.subtle.digest("SHA-256", data);
  const bytes = new Uint8Array(hash);
  return Array.from(bytes.slice(0, 4))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

/**
 * Log a usage data point to the Analytics Engine dataset.
 * Designed to be called via ctx.waitUntil() so it never blocks the response.
 */
/**
 * Log a usage data point to the Analytics Engine dataset.
 * Designed to be called via ctx.waitUntil() so it never blocks the response.
 *
 * Schema:
 *   blob1  = object key (path)
 *   blob2  = user-agent
 *   blob3  = hashed client IP
 *   blob4  = HTTP method
 *   blob5  = client IP (for geolocation)
 *   double1 = status code
 *   double2 = bytes transferred
 */
export async function logUsage(
  env: Env,
  request: Request,
  objectKey: string,
  statusCode: number,
  bytesTransferred: number,
): Promise<void> {
  const ip = request.headers.get("cf-connecting-ip") ?? "unknown";
  const hashedIp = await hashIp(ip);
  const userAgent = request.headers.get("user-agent") ?? "";

  env.USAGE.writeDataPoint({
    indexes: [objectKey],
    blobs: [objectKey, userAgent, hashedIp, request.method, ip],
    doubles: [statusCode, bytesTransferred],
  });
}
