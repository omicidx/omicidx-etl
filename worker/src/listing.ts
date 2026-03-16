/**
 * Generate a directory listing for a given R2 prefix.
 * Returns HTML if the client accepts it, otherwise JSON.
 */
export async function listDirectory(
  bucket: R2Bucket,
  prefix: string,
  acceptsHtml: boolean,
): Promise<Response> {
  const directories: string[] = [];
  const files: { key: string; size: number; lastModified: string }[] = [];

  let cursor: string | undefined;
  do {
    const listed = await bucket.list({ prefix, delimiter: "/", cursor });
    for (const obj of listed.objects) {
      files.push({
        key: obj.key,
        size: obj.size,
        lastModified: obj.uploaded.toISOString(),
      });
    }
    for (const dp of listed.delimitedPrefixes) {
      directories.push(dp);
    }
    cursor = listed.truncated ? listed.cursor : undefined;
  } while (cursor);

  if (acceptsHtml) {
    return htmlListing(prefix, directories, files);
  }

  return Response.json({ prefix, directories, files }, {
    headers: { "access-control-allow-origin": "*" },
  });
}

function htmlListing(
  prefix: string,
  directories: string[],
  files: { key: string; size: number; lastModified: string }[],
): Response {
  const title = prefix ? `Index of /${prefix}` : "OmicIDX Data";
  const parentLink = prefix
    ? `<a href="/${prefix.replace(/[^/]+\/$/, "")}">../</a>\n`
    : "";

  const dirLinks = directories
    .map((d) => `<a href="/${d}">${d.replace(prefix, "")}</a>`)
    .join("\n");

  const fileLinks = files
    .map((f) => {
      const name = f.key.replace(prefix, "");
      const size = formatBytes(f.size);
      const date = f.lastModified.slice(0, 10);
      return `<a href="/${f.key}">${name}</a>  ${size.padStart(10)}  ${date}`;
    })
    .join("\n");

  const html = `<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>${title}</title></head>
<body>
<h1>${title}</h1>
<pre>
${parentLink}${dirLinks}
${fileLinks}
</pre>
</body>
</html>`;

  return new Response(html, {
    headers: {
      "content-type": "text/html; charset=utf-8",
      "access-control-allow-origin": "*",
    },
  });
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  const val = bytes / Math.pow(1024, i);
  return `${val.toFixed(1)} ${units[i]}`;
}
