/**
 * Authentication utilities for token management
 */

export interface TokenInfo {
  token: string | null
  isValid: boolean
  isExpired: boolean
  payload?: any
  error?: string
}

/**
 * Get detailed information about the stored auth token
 */
export function getTokenInfo(): TokenInfo {
  // Try to get token from the new key first, then fallback to old key for migration
  let token = localStorage.getItem("access_token")

  // Migration: if token not found in new key, check old key
  if (!token) {
    token = localStorage.getItem("auth_token")
    if (token) {
      // Migrate to new key and remove old key
      localStorage.setItem("access_token", token)
      localStorage.removeItem("auth_token")
    }
  }

  if (!token) {
    return {
      token: null,
      isValid: false,
      isExpired: false,
      error: "No token found in localStorage"
    }
  }

  try {
    // Decode JWT payload (without verification)
    const parts = token.split('.')
    if (parts.length !== 3) {
      return {
        token,
        isValid: false,
        isExpired: false,
        error: "Invalid JWT format"
      }
    }

    const payload = JSON.parse(atob(parts[1]))
    const now = Math.floor(Date.now() / 1000)
    const isExpired = payload.exp && payload.exp < now

    return {
      token,
      isValid: true,
      isExpired,
      payload,
      error: isExpired ? "Token is expired" : undefined
    }
  } catch (error) {
    return {
      token,
      isValid: false,
      isExpired: false,
      error: `Failed to decode token: ${error instanceof Error ? error.message : 'Unknown error'}`
    }
  }
}

/**
 * Check if user is properly authenticated
 */
export function isAuthenticated(): boolean {
  const tokenInfo = getTokenInfo()
  return tokenInfo.isValid && !tokenInfo.isExpired
}

/**
 * Get auth headers for API requests
 */
export function getAuthHeaders(): HeadersInit {
  const tokenInfo = getTokenInfo()

  return {
    "Content-Type": "application/json",
    ...(tokenInfo.token && {
      "Authorization": `Bearer ${tokenInfo.token}`,
      "X-API-AUTH": `Bearer ${tokenInfo.token}`
    }),
  }
}

/**
 * Store authentication token
 */
export function setAuthToken(token: string): void {
  localStorage.setItem("access_token", token)
}

/**
 * Store refresh token
 */
export function setRefreshToken(token: string): void {
  localStorage.setItem("refresh_token", token)
}

/**
 * Get stored refresh token
 */
export function getRefreshToken(): string | null {
  return localStorage.getItem("refresh_token")
}

/**
 * Clear all authentication data
 */
export function clearAuthData(): void {
  localStorage.removeItem("access_token")
  localStorage.removeItem("auth_token") // Remove old key as well for cleanup
  localStorage.removeItem("refresh_token")
  localStorage.removeItem("user_data")
}

/**
 * Get the raw access token without validation
 */
export function getAccessToken(): string | null {
  // Try to get token from the new key first, then fallback to old key for migration
  let token = localStorage.getItem("access_token")

  // Migration: if token not found in new key, check old key
  if (!token) {
    token = localStorage.getItem("auth_token")
    if (token) {
      // Migrate to new key and remove old key
      localStorage.setItem("access_token", token)
      localStorage.removeItem("auth_token")
    }
  }

  return token
}
