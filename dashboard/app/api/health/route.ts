/**
 * Health check endpoint for production monitoring
 * Used by Docker healthcheck and load balancers
 */
export async function GET() {
  return Response.json({
    status: 'ok',
    service: 'stakazo-dashboard',
    timestamp: new Date().toISOString(),
  });
}
