'use client';

import { useRouter, useParams } from 'next/navigation';
import { ArrowLeft, Package } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ItemForm } from '@/features/item/components/ItemForm';
import { useItem } from '@/features/item/api/queries';
import { Skeleton } from '@/components/ui/skeleton';

export default function EditItemPage() {
  const router = useRouter();
  const params = useParams();
  const itemId = params.id as string;

  const { data: item, isLoading } = useItem(itemId);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-10" />
          <div className="space-y-2">
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-4 w-64" />
          </div>
        </div>
        <Skeleton className="h-[400px] w-full" />
      </div>
    );
  }

  if (!item) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button
            variant="outline"
            size="icon"
            onClick={() => router.push('/dashboard/items')}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Item Not Found</h1>
            <p className="text-muted-foreground">
              The item you are looking for does not exist
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button
          variant="outline"
          size="icon"
          onClick={() => router.push('/dashboard/items')}
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Edit Item</h1>
          <p className="text-muted-foreground">
            Update item details for "{item.title}"
          </p>
        </div>
      </div>

      {/* Item Form */}
      <ItemForm mode="update" item={item} />
    </div>
  );
}
