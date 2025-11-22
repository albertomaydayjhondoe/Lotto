import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"

export function middleware(request: NextRequest) {
  const token = request.cookies.get("auth_token")?.value || 
                request.headers.get("authorization")?.replace("Bearer ", "")

  // Check if accessing dashboard routes
  if (request.nextUrl.pathname.startsWith("/dashboard")) {
    // Allow login page
    if (request.nextUrl.pathname === "/dashboard/login") {
      return NextResponse.next()
    }

    // Check for token in localStorage (client-side check will handle this)
    // For now, allow access and let client-side handle auth
    return NextResponse.next()
  }

  return NextResponse.next()
}

export const config = {
  matcher: ["/dashboard/:path*"],
}
