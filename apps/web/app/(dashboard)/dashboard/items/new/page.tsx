'use client';

import { useRouter } from 'next/navigation';
import { ArrowLeft, Package } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ItemForm } from '@/features/item/components/ItemForm';

export default function NewItemPage() {
  const router = useRouter();

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
          <h1 className="text-3xl font-bold tracking-tight">Create Item</h1>
          <p className="text-muted-foreground">
            Add a new item to your inventory
          </p>
        </div>
      </div>

      {/* Item Form */}
      <ItemForm mode="create" />
    </div>
  );
}
