// The refresh token lives entirely in an httpOnly cookie the browser
// manages on its own - this module never sees it. The access token used
// to be persisted here too (in localStorage, alongside the refresh token),
// which meant any XSS anywhere in the app could read a long-lived
// credential straight out of browser storage. It's now kept only in this
// module-level variable: it doesn't survive a page reload, but that's the
// point - a reload just triggers a silent refresh (see AuthContext) using
// the httpOnly cookie an attacker's script can't touch either way.
let accessToken: string | null = null;

// The CSRF token that has to accompany refresh/logout calls (see backend
// accounts/cookies.py) can't be a second cookie the way this pattern
// usually works: the API lives on a different origin than this app, and
// cookies aren't readable across origins - the backend hands the value
// back in the login/register/refresh response body instead.
//
// Unlike the tokens above, this one is deliberately kept in localStorage
// rather than only in memory, so it survives a page reload the same way
// the httpOnly cookie does - otherwise every reload would show the app as
// logged out until the *next* one. That's safe specifically because this
// value's only job is proving a request came from this app's own
// same-origin JS, which is exactly what read access to this app's
// localStorage already means. It protects against a forged cross-site
// request, not against XSS on this app - any script that could read it
// here could just as easily call the API directly with the browser's
// cookies attached, CSRF token or not.
const CSRF_STORAGE_KEY = "refresh_csrf_token";

export const tokenStore = {
  getAccessToken(): string | null {
    return accessToken;
  },

  setAccessToken(token: string | null): void {
    accessToken = token;
  },

  getRefreshCsrfToken(): string | null {
    try {
      return localStorage.getItem(CSRF_STORAGE_KEY);
    } catch {
      return null;
    }
  },

  setRefreshCsrfToken(token: string | null): void {
    try {
      if (token) {
        localStorage.setItem(CSRF_STORAGE_KEY, token);
      } else {
        localStorage.removeItem(CSRF_STORAGE_KEY);
      }
    } catch {
      // Storage can be unavailable (private browsing, quota, etc.) - the
      // session still works within the current page load either way,
      // it just won't survive a reload.
    }
  },

  clear(): void {
    accessToken = null;
    tokenStore.setRefreshCsrfToken(null);
  },
};
