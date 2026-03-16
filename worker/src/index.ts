import { logUsage } from "./analytics";
import { listDirectory } from "./listing";

export interface Env {
  DATA_BUCKET: R2Bucket;
  USAGE: AnalyticsEngineDataset;
}

/** Map file extensions to content types. */
function contentType(key: string): string {
  if (key.endsWith(".parquet")) return "application/vnd.apache.parquet";
  if (key.endsWith(".json") || key.endsWith(".ndjson"))
    return "application/json";
  if (key.endsWith(".gz")) return "application/gzip";
  if (key.endsWith(".csv")) return "text/csv";
  return "application/octet-stream";
}

const CORS_HEADERS = {
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET, HEAD, OPTIONS",
  "access-control-allow-headers": "*",
};

export default {
  async fetch(
    request: Request,
    env: Env,
    ctx: ExecutionContext,
  ): Promise<Response> {
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: CORS_HEADERS });
    }

    if (request.method !== "GET" && request.method !== "HEAD") {
      return new Response("Method not allowed", { status: 405 });
    }

    const url = new URL(request.url);
    const key = decodeURIComponent(url.pathname.slice(1)); // strip leading /

    // Directory listing
    if (key === "" || key.endsWith("/")) {
      const acceptsHtml =
        request.headers.get("accept")?.includes("text/html") ?? false;
      const response = await listDirectory(env.DATA_BUCKET, key, acceptsHtml);
      ctx.waitUntil(logUsage(env, request, key || "/", response.status));
      return response;
    }

    // Serve object from R2
    const object = await env.DATA_BUCKET.get(key, {
      onlyIf: request.headers,
    });

    if (object === null) {
      ctx.waitUntil(logUsage(env, request, key, 404));
      return new Response("Not found", {
        status: 404,
        headers: CORS_HEADERS,
      });
    }

    // R2 returns R2ObjectBody (has body) or R2Object (conditional 304)
    if (!("body" in object)) {
      ctx.waitUntil(logUsage(env, request, key, 304));
      return new Response(null, {
        status: 304,
        headers: {
          etag: object.httpEtag,
          ...CORS_HEADERS,
        },
      });
    }

    const headers = new Headers({
      "content-type": contentType(key),
      etag: object.httpEtag,
      "cache-control": "public, max-age=86400",
      ...CORS_HEADERS,
    });

    if (object.size !== undefined) {
      headers.set("content-length", object.size.toString());
    }

    ctx.waitUntil(logUsage(env, request, key, 200));

    return new Response(request.method === "HEAD" ? null : object.body, {
      status: 200,
      headers,
    });
  },
} satisfies ExportedHandler<Env>;
