// The refresh token lives entirely in an httpOnly cookie the browser
// manages on its own - this module never sees it. The access token used
// to be persisted here too (in localStorage, alongside the refresh token),
// which meant any XSS anywhere in the app could read a long-lived
// credential straight out of browser storage. It's now kept only in this
// module-level variable: it doesn't survive a page reload, but that's the
// point - a reload just triggers a silent refresh (see AuthContext) using
// the httpOnly cookie the attacker's script can't touch either way.
let accessToken: string | null = null;

const REFRESH_CSRF_COOKIE_NAME = "refresh_csrf_token";

function readCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp(`(?:^|;\\s*)${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

export const tokenStore = {
  getAccessToken(): string | null {
    return accessToken;
  },

  setAccessToken(token: string | null): void {
    accessToken = token;
  },

  // Read by requests to /auth/refresh/ and /auth/logout/ - the backend
  // rejects those unless this exact value comes back as a header, which a
  // forged cross-site request has no way to read (double-submit CSRF
  // defense; see backend accounts/cookies.py).
  getRefreshCsrfToken(): string | null {
    return readCookie(REFRESH_CSRF_COOKIE_NAME);
  },
};
