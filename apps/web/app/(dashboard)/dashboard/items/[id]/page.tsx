"use client";

import { useParams } from "next/navigation";
import { ItemDetail } from "@/features/item/client";
import { Suspense } from "react";
import { Skeleton } from "@/components/ui/skeleton";

export default function ItemPage() {
  const params = useParams();
  const itemId = params.id as string;

  return (
    <Suspense fallback={<ItemDetailSkeleton />}>
      <ItemDetail itemId={itemId} />
    </Suspense>
  );
}

function ItemDetailSkeleton() {
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
