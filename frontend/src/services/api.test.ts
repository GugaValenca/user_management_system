import MockAdapter from "axios-mock-adapter";
import axios from "axios";
import api, { authAPI } from "./api";
import { tokenStore } from "../utils/tokenStore";

const clearCookies = () => {
  document.cookie.split(";").forEach((cookie) => {
    const name = cookie.split("=")[0].trim();
    if (name) {
      document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/`;
    }
  });
};

describe("api refresh flow", () => {
  let mock: MockAdapter;
  let rootMock: MockAdapter;

  beforeEach(() => {
    clearCookies();
    tokenStore.setAccessToken(null);
    mock = new MockAdapter(api);
    rootMock = new MockAdapter(axios);
  });

  afterEach(() => {
    mock.restore();
    rootMock.restore();
  });

  it("retries the original request with a new access token after a 401", async () => {
    tokenStore.setAccessToken("expired-token");
    document.cookie = "refresh_csrf_token=csrf-value";

    mock.onGet("/auth/profile/").replyOnce(401).onGet("/auth/profile/").reply(200, {
      id: 1,
      email: "user@example.com",
    });
    rootMock.onPost(/\/auth\/refresh\/$/).reply((config) => {
      expect(config.headers?.["X-Refresh-Csrf-Token"]).toBe("csrf-value");
      return [200, { access: "new-access-token" }];
    });

    const profile = await authAPI.getProfile();

    expect(profile).toEqual({ id: 1, email: "user@example.com" });
    expect(tokenStore.getAccessToken()).toBe("new-access-token");
  });

  it("redirects to login when the refresh token itself is rejected", async () => {
    tokenStore.setAccessToken("expired-token");

    mock.onGet("/auth/profile/").reply(401);
    rootMock.onPost(/\/auth\/refresh\/$/).reply(401);

    const originalLocation = window.location;
    // @ts-expect-error - narrowing window.location for this test only
    delete window.location;
    window.location = { ...originalLocation, href: "" } as Location;

    await expect(authAPI.getProfile()).rejects.toBeTruthy();

    expect(window.location.href).toBe("/login");
    expect(tokenStore.getAccessToken()).toBeNull();

    window.location = originalLocation;
  });

  it("does not attempt a refresh loop when the refresh endpoint itself 401s", async () => {
    tokenStore.setAccessToken("expired-token");
    mock.onGet("/auth/profile/").reply(401);
    rootMock.onPost(/\/auth\/refresh\/$/).replyOnce(401);

    const originalLocation = window.location;
    // @ts-expect-error - narrowing window.location for this test only
    delete window.location;
    window.location = { ...originalLocation, href: "" } as Location;

    await expect(authAPI.getProfile()).rejects.toBeTruthy();

    // Only one refresh attempt should have been made.
    expect(rootMock.history.post.length).toBe(1);

    window.location = originalLocation;
  });

  it("sends the refresh CSRF cookie's value as a header on logout", async () => {
    document.cookie = "refresh_csrf_token=logout-csrf-value";
    mock.onPost("/auth/logout/").reply((config) => {
      expect(config.headers?.["X-Refresh-Csrf-Token"]).toBe("logout-csrf-value");
      return [200, {}];
    });

    await authAPI.logout();
  });
});
