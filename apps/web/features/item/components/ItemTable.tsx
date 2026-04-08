'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Skeleton } from '@/components/ui/skeleton';
import { MoreHorizontal, Pencil, Trash2, Package, ChevronLeft, ChevronRight } from 'lucide-react';
import { useItems, useDeleteItem } from '../api/queries';
import type { ItemPublic } from '@repo/sdk';

interface ItemTableProps {
  skip?: number;
  limit?: number;
  page?: number;
  onPageChange?: (page: number) => void;
  showOwner?: boolean;
}

export function ItemTable({ 
  skip = 0, 
  limit = 10, 
  page = 1, 
  onPageChange,
  showOwner = false 
}: ItemTableProps) {
  const router = useRouter();
  const { data, isLoading } = useItems(skip, limit);
  const deleteMutation = useDeleteItem();
  
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [itemToDelete, setItemToDelete] = useState<ItemPublic | null>(null);

  const items = data?.data || [];
  const total = data?.count || 0;
  const totalPages = Math.ceil(total / limit);

  const handleDeleteClick = (item: ItemPublic) => {
    setItemToDelete(item);
    setDeleteDialogOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (itemToDelete) {
      try {
        await deleteMutation.mutateAsync(itemToDelete.id);
        toast.success('Item deleted successfully');
      } catch (error) {
        toast.error('Failed to delete item');
      }
    }
    setDeleteDialogOpen(false);
    setItemToDelete(null);
  };

  if (isLoading) {
    return (
      <div className="space-y-2">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
      </div>
    );
  }

  return (
    <>
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Title</TableHead>
              <TableHead>Description</TableHead>
              {showOwner && <TableHead>Owner</TableHead>}
              <TableHead>Created</TableHead>
              <TableHead className="w-[50px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.length === 0 ? (
              <TableRow>
                <TableCell colSpan={showOwner ? 5 : 4} className="text-center py-8 text-muted-foreground">
                  No items found. Create your first item to get started.
                </TableCell>
              </TableRow>
            ) : (
              items.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Package className="h-4 w-4 text-muted-foreground" />
                      <span className="font-medium">{item.title}</span>
                    </div>
                  </TableCell>
                  <TableCell className="max-w-xs truncate">
                    {item.description || '-'}
                  </TableCell>
                  {showOwner && (
                    <TableCell>
                      <Badge variant="outline">{item.owner_id}</Badge>
                    </TableCell>
                  )}
                  <TableCell>
                    {item.created_at
                      ? new Date(item.created_at).toLocaleDateString('en-US')
                      : '-'}
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem asChild>
                          <Link href={`/dashboard/items/${item.id}/edit`}>
                            <Pencil className="mr-2 h-4 w-4" />
                            Edit
                          </Link>
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          className="text-destructive"
                          onClick={() => handleDeleteClick(item)}
                        >
                          <Trash2 className="mr-2 h-4 w-4" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Showing {skip + 1} to {Math.min(skip + limit, total)} of {total} items
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange?.(page - 1)}
              disabled={page <= 1}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <span className="text-sm">
              Page {page} of {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange?.(page + 1)}
              disabled={page >= totalPages}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm Delete</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{itemToDelete?.title}"? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleConfirmDelete}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

// Keep the old interface for backward compatibility
interface ItemTableLegacyProps {
  items: ItemPublic[];
  isLoading?: boolean;
  onDelete?: (itemId: string) => void;
  showOwner?: boolean;
}

export function ItemTableLegacy({ items, isLoading, onDelete, showOwner = false }: ItemTableLegacyProps) {
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [itemToDelete, setItemToDelete] = useState<ItemPublic | null>(null);

  const handleDeleteClick = (item: ItemPublic) => {
    setItemToDelete(item);
    setDeleteDialogOpen(true);
  };

  const handleConfirmDelete = () => {
    if (itemToDelete && onDelete) {
      onDelete(itemToDelete.id);
    }
    setDeleteDialogOpen(false);
    setItemToDelete(null);
  };

  if (isLoading) {
    return (
      <div className="space-y-2">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
      </div>
    );
  }

  return (
    <>
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Title</TableHead>
              <TableHead>Description</TableHead>
              {showOwner && <TableHead>Owner</TableHead>}
              <TableHead>Created</TableHead>
              <TableHead className="w-[50px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.length === 0 ? (
              <TableRow>
                <TableCell colSpan={showOwner ? 5 : 4} className="text-center py-8 text-muted-foreground">
                  No items found
                </TableCell>
              </TableRow>
            ) : (
              items.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Package className="h-4 w-4 text-muted-foreground" />
                      <span className="font-medium">{item.title}</span>
                    </div>
                  </TableCell>
                  <TableCell className="max-w-xs truncate">
                    {item.description || '-'}
                  </TableCell>
                  {showOwner && (
                    <TableCell>
                      <Badge variant="outline">{item.owner_id}</Badge>
                    </TableCell>
                  )}
                  <TableCell>
                    {item.created_at
                      ? new Date(item.created_at).toLocaleDateString('en-US')
                      : '-'}
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem asChild>
                          <Link href={`/dashboard/items/${item.id}/edit`}>
                            <Pencil className="mr-2 h-4 w-4" />
                            Edit
                          </Link>
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          className="text-destructive"
                          onClick={() => handleDeleteClick(item)}
                        >
                          <Trash2 className="mr-2 h-4 w-4" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm Delete</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{itemToDelete?.title}"? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleConfirmDelete}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
