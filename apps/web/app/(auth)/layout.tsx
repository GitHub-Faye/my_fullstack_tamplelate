"use client";

import type { ReactNode } from "react";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useIsAuthenticated, useIsHydrated, useCurrentUser } from "@/features/user";
import { Loader2 } from "lucide-react";

export default function AuthLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const isAuthenticated = useIsAuthenticated();
  const isHydrated = useIsHydrated();
  const user = useCurrentUser();

  useEffect(() => {
    if (isHydrated && isAuthenticated) {
      if (user?.role === "pm") {
        router.replace("/pm");
      } else if (user?.role === "engineer") {
        router.replace("/engineer");
      } else if (user?.role === "admin") {
        router.replace("/admin");
      } else {
        router.replace("/admin");
      }
    }
  }, [isHydrated, isAuthenticated, user?.role, router]);

  // Show loading while store is hydrating
  if (!isHydrated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-muted/50 p-4">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  // If authenticated, show loading (will redirect)
  if (isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-muted/50 p-4">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/50 p-4">
      <div className="w-full max-w-md">{children}</div>
    </div>
  );
}
