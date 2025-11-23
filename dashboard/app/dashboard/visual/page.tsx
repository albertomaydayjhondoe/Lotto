/**
 * Visual Analytics Main Page (PASO 8.4)
 * 
 * Redirects to overview page
 */

'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { LoadingState } from '@/components/visual_analytics';

export default function VisualAnalyticsPage() {
  const router = useRouter();

  useEffect(() => {
    router.push('/dashboard/visual/overview');
  }, [router]);

  return (
    <div className="container mx-auto py-8">
      <LoadingState message="Redirecting to analytics overview..." />
    </div>
  );
}
