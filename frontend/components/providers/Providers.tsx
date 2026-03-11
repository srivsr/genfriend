'use client';

import { ReactNode, useEffect } from 'react';
import { ClerkProvider, useAuth as useClerkAuth } from '@clerk/nextjs';
import { setClerkToken } from '@/lib/api-client';
import PWAProvider from '@/components/pwa/PWAProvider';
import InstallPrompt from '@/components/pwa/InstallPrompt';

const clerkKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;

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
  const inner = (
    <PWAProvider>
      {children}
      <InstallPrompt />
    </PWAProvider>
  );

  if (!clerkKey) {
    return inner;
  }

  return (
    <ClerkProvider publishableKey={clerkKey}>
      <ClerkTokenSync>
        {inner}
      </ClerkTokenSync>
    </ClerkProvider>
  );
}
