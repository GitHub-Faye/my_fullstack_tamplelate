"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useIsAuthenticated, useIsHydrated, useCurrentUser } from "@/features/user";
import { Loader2 } from "lucide-react";

export default function Home() {
  const router = useRouter();
  const isAuthenticated = useIsAuthenticated();
  const isHydrated = useIsHydrated();
  const user = useCurrentUser();

  useEffect(() => {
    if (isHydrated) {
      if (isAuthenticated) {
        // 根据角色跳转到对应工作台
        if (user?.role === "pm") {
          router.replace("/pm");
        } else if (user?.role === "engineer") {
          router.replace("/engineer");
        } else if (user?.role === "admin") {
          router.replace("/admin");
        } else {
          router.replace("/dashboard");
        }
      } else {
        router.replace("/login");
      }
    }
  }, [isHydrated, isAuthenticated, user?.role, router]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <Loader2 className="h-8 w-8 animate-spin" />
    </div>
  );
}