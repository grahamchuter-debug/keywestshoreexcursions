/**
 * Routing only. Page copy lives in public HTML.
 * Preview Worker only in 29B — live Pages project still owns custom domains.
 * When public host is seen: HTTP and www must 301 to HTTPS apex.
 */
const APEX = "keywestshoreexcursions.com";
const WWW = "www.keywestshoreexcursions.com";

function publicHost(hostname) {
  return hostname === WWW || hostname === APEX;
}

function requestHost(request, url) {
  const raw = request.headers.get("Host") || url.hostname;
  return String(raw).split(":")[0].toLowerCase();
}

function stripHtml(pathname) {
  let path = pathname || "/";
  if (path.length > 1 && path.endsWith("/")) path = path.slice(0, -1);
  if (path === "/index.html") path = "/";
  else if (path.endsWith(".html")) path = path.slice(0, -".html".length);
  return path;
}

function redirectTo(pathname, search = "") {
  const location = `https://${APEX}${pathname}${search}`;
  return new Response(null, {
    status: 301,
    headers: { Location: location },
  });
}

function redirectLocal(url, pathname) {
  const port =
    !url.port || (url.protocol === "http:" && url.port === "80") || (url.protocol === "https:" && url.port === "443")
      ? ""
      : `:${url.port}`;
  const scheme = url.protocol.replace(":", "");
  const location = `${scheme}://${url.hostname}${port}${pathname}${url.search || ""}`;
  return new Response(null, {
    status: 301,
    headers: { Location: location },
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const host = requestHost(request, url);
    const path = stripHtml(url.pathname);
    const isPublic = publicHost(host);

    // Public hosts always land on HTTPS apex, single hop.
    if (isPublic && (host === WWW || url.protocol === "http:" || path !== url.pathname)) {
      return redirectTo(path, url.search || "");
    }

    // Local/preview: normalize path shape only.
    if (!isPublic && path !== url.pathname) {
      return redirectLocal(url, path);
    }

    if (path === "/404") {
      return notFound(request, env, host);
    }

    if (path === "/" || !path.includes(".")) {
      const assetUrl = new URL(request.url);
      assetUrl.pathname = path === "/" ? "/index.html" : `${path}.html`;
      const page = await env.ASSETS.fetch(new Request(assetUrl.toString(), { method: "GET" }));
      if (page.ok) return decorate(page, host);
      return notFound(request, env, host);
    }

    const asset = await env.ASSETS.fetch(request);
    if (asset.status === 404) return notFound(request, env, host);
    return decorate(asset, host);
  },
};

function decorate(response, hostname) {
  if (publicHost(hostname) && hostname === APEX) return response;
  const headers = new Headers(response.headers);
  if (!publicHost(hostname)) headers.set("X-Robots-Tag", "noindex");
  return new Response(response.body, { status: response.status, headers });
}

async function notFound(request, env, hostname) {
  const fileUrl = new URL("/404.html", request.url);
  const page = await env.ASSETS.fetch(new Request(fileUrl.toString(), { method: "GET" }));
  const headers = new Headers(page.headers);
  headers.set("X-Robots-Tag", "noindex");
  headers.delete("Location");
  if (!publicHost(String(hostname || "").toLowerCase())) headers.set("X-Robots-Tag", "noindex");
  return new Response(page.body, { status: 404, headers });
}
