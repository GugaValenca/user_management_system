// The refresh token lives entirely in an httpOnly cookie the browser
// manages on its own - this module never sees it. The access token used
// to be persisted here too (in localStorage, alongside the refresh token),
// which meant any XSS anywhere in the app could read a long-lived
// credential straight out of browser storage. It's now kept only in this
// module-level variable: it doesn't survive a page reload, but that's the
// point - a reload just triggers a silent refresh (see AuthContext) using
// the httpOnly cookie an attacker's script can't touch either way.
//
// The CSRF token that has to accompany refresh/logout calls (see backend
// accounts/cookies.py) is kept the same way, for the same reason it can't
// just be a second cookie: the API lives on a different origin than this
// app, and cookies aren't readable across origins - the backend hands the
// value back in the login/register/refresh response body instead, which
// only this app's own JS ever gets to read.
let accessToken: string | null = null;
let refreshCsrfToken: string | null = null;

export const tokenStore = {
  getAccessToken(): string | null {
    return accessToken;
  },

  setAccessToken(token: string | null): void {
    accessToken = token;
  },

  getRefreshCsrfToken(): string | null {
    return refreshCsrfToken;
  },

  setRefreshCsrfToken(token: string | null): void {
    refreshCsrfToken = token;
  },

  clear(): void {
    accessToken = null;
    refreshCsrfToken = null;
  },
};
