import { NextRequest, NextResponse } from 'next/server'
import { AccessToken } from 'livekit-server-sdk'

export interface ConnectionDetails {
  serverUrl: string
  participantToken: string
  participantName: string
  roomName: string
}

export async function GET(request: NextRequest) {
  try {
    // Validate required environment variables
    const apiKey = process.env.LIVEKIT_API_KEY
    const apiSecret = process.env.LIVEKIT_API_SECRET
    const serverUrl = process.env.NEXT_PUBLIC_LIVEKIT_URL

    if (!apiKey || !apiSecret || !serverUrl) {
      return NextResponse.json(
        { error: 'Livekit credentials not configured' },
        { status: 500 }
      )
    }

    // Get auth token from headers to verify user is authenticated
    const authHeader = request.headers.get('authorization')
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return NextResponse.json(
        { error: 'Authentication required' },
        { status: 401 }
      )
    }

    // Generate unique room and participant names
    const roomName = `voice-session-${Date.now()}`
    const participantName = `user-${Date.now()}`

    // Create Livekit access token
    const token = new AccessToken(apiKey, apiSecret, {
      identity: participantName,
      ttl: '1h', // Token valid for 1 hour
    })

    // Grant permissions
    token.addGrant({
      room: roomName,
      roomJoin: true,
      canPublish: true,
      canSubscribe: true,
      canPublishData: true,
    })

    const jwt = await token.toJwt()

    const connectionDetails: ConnectionDetails = {
      serverUrl,
      participantToken: jwt,
      participantName,
      roomName,
    }

    return NextResponse.json(connectionDetails)
  } catch (error) {
    console.error('Error creating connection details:', error)
    return NextResponse.json(
      { error: 'Failed to create connection details' },
      { status: 500 }
    )
  }
}
