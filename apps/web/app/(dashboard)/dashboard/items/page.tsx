'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Plus, Package } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ItemTable } from '@/features/item/components/ItemTable';

export default function ItemsPage() {
  const router = useRouter();
  const [page, setPage] = useState(1);
  const limit = 10;
  const skip = (page - 1) * limit;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Items</h1>
          <p className="text-muted-foreground">
            Manage your items and inventory
          </p>
        </div>
        <Button onClick={() => router.push('/dashboard/items/new')}>
          <Plus className="mr-2 h-4 w-4" />
          New Item
        </Button>
      </div>

      {/* Items Table */}
      <ItemTable
        skip={skip}
        limit={limit}
        page={page}
        onPageChange={setPage}
      />
    </div>
  );
}
