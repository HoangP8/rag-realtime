"use client"

import LoginForm from "@/components/login-form"
import { useRouter } from "next/navigation"

export default function LoginPage() {
  const router = useRouter()
  
  const handleLogin = (user: any) => {
    // After successful login, redirect to the main page
    router.push("/")
  }

  return <LoginForm onLogin={handleLogin} />
}