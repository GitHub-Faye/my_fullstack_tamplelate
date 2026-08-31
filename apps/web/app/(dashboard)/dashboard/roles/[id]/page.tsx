"use client";

import { useParams } from "next/navigation";
import { RoleDetail } from "@/features/role/client";
import { Suspense } from "react";
import { Skeleton } from "@/components/ui/skeleton";

export default function RolePage() {
  const params = useParams();
  const roleId = params.id as string;

  return (
    <Suspense fallback={<RoleDetailSkeleton />}>
      <RoleDetail roleId={roleId} />
    </Suspense>
  );
}

function RoleDetailSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-10 w-32" />
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-2/3" />
      </div>
    </div>
  );
}
