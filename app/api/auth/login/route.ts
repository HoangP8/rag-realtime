import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const { email, password } = await request.json()

    // Validate input check if it entered or not
    if (!email|| !password) {
      return NextResponse.json({ error: "Email and password are required" }, { status: 400 })
    }

    // Make request to your Fly.io hosted server
    const flyServerUrl = process.env.FLY_SERVER_URL || "https://medbot-backend.fly.dev"
    const response = await fetch(`${flyServerUrl}/api/v1/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email,
        password,
      }),
    })

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json({ error: data.message || "Authentication failed" }, { status: response.status })
    }

    // Return success response with user data and token
    return NextResponse.json({
      success: true,
      user: data.user,
      token: data.token,
      message: "Login successful",
    })
  } catch (error) {
    console.error("Login API error:", error)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}
