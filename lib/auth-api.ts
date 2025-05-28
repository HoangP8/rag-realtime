import {
  setAuthToken,
  setRefreshToken,
  getAccessToken,
  clearAuthData
} from '@/lib/auth-utils'

interface LoginCredentials {
  email: string
  password: string
}

interface LoginResponse {
  access_token?: string,
  refresh_token?: string,
  token_type?: string,
  expires_at?: string,
  expires_in?: number,
  success?: boolean,
  error?: string
}

interface LogoutResponse {
  success: boolean
  message?: string
  error?: string
}

export class AuthAPI {
  private static baseUrl = "https://medbot-backend.fly.dev/api/v1/auth"

  static async login(credentials: LoginCredentials): Promise<LoginResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(credentials),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || "Login Failed")
      }

      // Store token in localStorage if login successful
      if (data.success && data.access_token) {
        setAuthToken(data.access_token)
        if (data.refresh_token) {
          setRefreshToken(data.refresh_token)
        }
      }

      return data
    } catch (error) {
      console.error("Login error:", error)
      return {
        success: false,
        error: error instanceof Error ? error.message : "Login Not succeed",
      }
    }
  }

  static async logout(): Promise<LogoutResponse> {
    try {
      const token = getAccessToken()

      if (!token) {
        // Clear local storage even if no token
        clearAuthData()
        return { success: true, message: "Logged out successfully" }
      }

      const response = await fetch(`${this.baseUrl}/logout`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ token }),
      })

      const data = await response.json()

      // Clear auth data regardless of server response
      clearAuthData()

      if (!response.ok) {
        console.warn("Logout warning:", data.error)
        // Still return success since we cleared local data
        return { success: true, message: "Logged out locally" }
      }

      return data
    } catch (error) {
      console.error("Logout error:", error)
      // Clear local data even on error
      clearAuthData()
      return {
        success: true,
        message: "Logged out locally due to error",
      }
    }
  }

  static clearAuthData(): void {
    clearAuthData()
  }

  static getStoredToken(): string | null {
    return getAccessToken()
  }

  static getStoredUser(): any | null {
    const userData = localStorage.getItem("user_data")
    return userData ? JSON.parse(userData) : null
  }

  static isAuthenticated(): boolean {
    return !!this.getStoredToken()
  }
}
