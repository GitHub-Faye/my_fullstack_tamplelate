'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Plus, Pencil, Trash2, Package } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  readItemsV1ItemsItemsGet,
  deleteItemV1ItemsItemsIdDelete,
} from '@repo/sdk';
import type { ItemPublic } from '@repo/sdk';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { toast } from 'sonner';

export default function ItemsPage() {
  const queryClient = useQueryClient();
  const [itemToDelete, setItemToDelete] = useState<ItemPublic | null>(null);

  const { data: itemsData, isLoading } = useQuery({
    queryKey: ['items'],
    queryFn: async () => {
      const response = await readItemsV1ItemsItemsGet();
      return response.data;
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (itemId: string) => {
      const response = await deleteItemV1ItemsItemsIdDelete({
        path: { id: itemId },
      });
      return response.data;
    },
    onSuccess: () => {
      toast.success('Item deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['items'] });
      setItemToDelete(null);
    },
    onError: (error) => {
      toast.error('Failed to delete item');
      console.error('Failed to delete item:', error);
    },
  });

  const handleDelete = (item: ItemPublic) => {
    setItemToDelete(item);
  };

  const confirmDelete = () => {
    if (itemToDelete) {
      deleteMutation.mutate(itemToDelete.id);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  const items = itemsData?.data || [];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Items</h1>
        <Button asChild>
          <Link href="/dashboard/items/new">
            <Plus className="mr-2 h-4 w-4" /> Create New Item
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>All Items</CardTitle>
        </CardHeader>
        <CardContent>
          {items.length === 0 ? (
            <div className="text-center py-12">
              <Package className="mx-auto h-12 w-12 text-muted-foreground" />
              <h3 className="mt-4 text-lg font-semibold">No items yet</h3>
              <p className="text-muted-foreground">Get started by creating a new item.</p>
              <Button className="mt-4" asChild>
                <Link href="/dashboard/items/new">
                  <Plus className="mr-2 h-4 w-4" /> Create New Item
                </Link>
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Title</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((item: ItemPublic) => (
                  <TableRow key={item.id}>
                    <TableCell className="font-medium">{item.title}</TableCell>
                    <TableCell className="max-w-xs truncate">
                      {item.description || '-'}
                    </TableCell>
                    <TableCell>
                      {item.created_at
                        ? new Date(item.created_at).toLocaleDateString()
                        : '-'}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end space-x-2">
                        <Button variant="outline" size="sm" asChild>
                          <Link href={`/dashboard/items/${item.id}/edit`}>
                            <Pencil className="h-4 w-4" />
                          </Link>
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDelete(item)}
                          disabled={deleteMutation.isPending}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <Dialog open={!!itemToDelete} onOpenChange={() => setItemToDelete(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Item</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{itemToDelete?.title}"? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setItemToDelete(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={confirmDelete}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
