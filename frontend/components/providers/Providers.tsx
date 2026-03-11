'use client';

import { ReactNode, useEffect } from 'react';
import { ClerkProvider, useAuth as useClerkAuth } from '@clerk/nextjs';
import { setClerkToken } from '@/lib/api-client';
import PWAProvider from '@/components/pwa/PWAProvider';
import InstallPrompt from '@/components/pwa/InstallPrompt';

// Check if Clerk has valid test keys for localhost
const hasValidClerkKey = typeof window !== 'undefined'
  ? process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY?.startsWith('pk_test_')
  : process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY?.startsWith('pk_test_');

function ClerkTokenSync({ children }: { children: ReactNode }) {
  const { getToken, isSignedIn } = useClerkAuth();

  useEffect(() => {
    async function syncToken() {
      if (isSignedIn) {
        try {
          const token = await getToken();
          setClerkToken(token);
        } catch (error) {
          console.error('Failed to get Clerk token:', error);
          setClerkToken(null);
        }
      } else {
        setClerkToken(null);
      }
    }

    syncToken();
  }, [isSignedIn, getToken]);

  return <>{children}</>;
}

export default function Providers({ children }: { children: ReactNode }) {
  // Skip Clerk if no valid test keys (using production keys on localhost won't work)
  if (!hasValidClerkKey) {
    return (
      <PWAProvider>
        {children}
        <InstallPrompt />
      </PWAProvider>
    );
  }

  return (
    <ClerkProvider>
      <ClerkTokenSync>
        <PWAProvider>
          {children}
          <InstallPrompt />
        </PWAProvider>
      </ClerkTokenSync>
    </ClerkProvider>
  );
}
