import MockAdapter from "axios-mock-adapter";
import axios from "axios";
import api, { authAPI } from "./api";
import { authStorage } from "../utils/authStorage";

describe("api refresh flow", () => {
  let mock: MockAdapter;
  let rootMock: MockAdapter;

  beforeEach(() => {
    localStorage.clear();
    mock = new MockAdapter(api);
    rootMock = new MockAdapter(axios);
  });

  afterEach(() => {
    mock.restore();
    rootMock.restore();
  });

  it("retries the original request with a new access token after a 401", async () => {
    authStorage.setTokens({ access: "expired-token", refresh: "valid-refresh-token" });

    mock.onGet("/auth/profile/").replyOnce(401).onGet("/auth/profile/").reply(200, {
      id: 1,
      email: "user@example.com",
    });
    rootMock.onPost(/\/auth\/refresh\/$/).reply(200, { access: "new-access-token" });

    const profile = await authAPI.getProfile();

    expect(profile).toEqual({ id: 1, email: "user@example.com" });
    expect(authStorage.getAccessToken()).toBe("new-access-token");
  });

  it("redirects to login when the refresh token itself is rejected", async () => {
    authStorage.setTokens({ access: "expired-token", refresh: "expired-refresh-token" });

    mock.onGet("/auth/profile/").reply(401);
    rootMock.onPost(/\/auth\/refresh\/$/).reply(401);

    const originalLocation = window.location;
    // @ts-expect-error - narrowing window.location for this test only
    delete window.location;
    window.location = { ...originalLocation, href: "" } as Location;

    await expect(authAPI.getProfile()).rejects.toBeTruthy();

    expect(window.location.href).toBe("/login");
    expect(authStorage.getAccessToken()).toBeNull();

    window.location = originalLocation;
  });

  it("does not attempt a refresh loop when the refresh endpoint itself 401s", async () => {
    authStorage.setTokens({ access: "expired-token", refresh: "expired-refresh-token" });
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
});
