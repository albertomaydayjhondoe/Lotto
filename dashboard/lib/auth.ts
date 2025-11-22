import jwt from "jsonwebtoken"

const JWT_SECRET = process.env.JWT_SECRET || "stakazo-dashboard-secret-key-2025"
const DASHBOARD_USER = process.env.DASHBOARD_USER || "admin"
const DASHBOARD_PASS = process.env.DASHBOARD_PASS || "1234"

export interface AuthToken {
  username: string
  exp: number
}

export const auth = {
  login: (username: string, password: string): string | null => {
    if (username === DASHBOARD_USER && password === DASHBOARD_PASS) {
      const token = jwt.sign(
        { username, exp: Math.floor(Date.now() / 1000) + 60 * 60 * 24 }, // 24h
        JWT_SECRET
      )
      return token
    }
    return null
  },

  verify: (token: string): AuthToken | null => {
    try {
      const decoded = jwt.verify(token, JWT_SECRET) as AuthToken
      return decoded
    } catch (error) {
      return null
    }
  },

  getToken: (): string | null => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("auth_token")
    }
    return null
  },

  setToken: (token: string): void => {
    if (typeof window !== "undefined") {
      localStorage.setItem("auth_token", token)
    }
  },

  removeToken: (): void => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("auth_token")
    }
  },

  isAuthenticated: (): boolean => {
    const token = auth.getToken()
    if (!token) return false
    return auth.verify(token) !== null
  },
}
