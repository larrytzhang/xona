"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

/**
 * Client-side providers wrapper for GPS Shield.
 *
 * Initializes React Query with sensible defaults for the app:
 *   - staleTime: 30 seconds (most data refreshes on polling).
 *   - retry: 2 attempts on failure.
 *
 * @param children - Child components that need access to React Query.
 * @returns Provider-wrapped children.
 */
export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30 * 1000,
            retry: 2,
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}
