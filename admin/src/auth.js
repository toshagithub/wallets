const TOKEN_KEY = "wallets_access_token";
const USER_KEY = "wallets_user";

export function saveSession(accessToken, user) {
  localStorage.setItem(TOKEN_KEY, accessToken);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function getSession() {
  const accessToken = localStorage.getItem(TOKEN_KEY);
  const user = localStorage.getItem(USER_KEY);

  if (!accessToken || !user) {
    return null;
  }

  return {
    accessToken,
    user: JSON.parse(user),
  };
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}
