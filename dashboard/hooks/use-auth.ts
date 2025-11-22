"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { auth } from "@/lib/auth"

export function useAuth() {
  const router = useRouter()

  useEffect(() => {
    if (!auth.isAuthenticated()) {
      router.push("/login")
    }
  }, [router])

  return {
    isAuthenticated: auth.isAuthenticated(),
    logout: () => {
      auth.removeToken()
      router.push("/login")
    },
  }
}
