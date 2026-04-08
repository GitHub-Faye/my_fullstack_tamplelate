'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { itemCreateSchema, itemUpdateSchema, type ItemCreateFormData, type ItemUpdateFormData } from '../schemas';
import { useCreateItem, useUpdateItem } from '../api/queries';
import type { ItemPublic } from '@repo/sdk';

interface ItemFormProps {
  mode: 'create' | 'update';
  item?: ItemPublic;
}

export function ItemForm({ mode, item }: ItemFormProps) {
  const router = useRouter();
  const createMutation = useCreateItem();
  const updateMutation = useUpdateItem();

  const isLoading = createMutation.isPending || updateMutation.isPending;

  const form = useForm<ItemCreateFormData | ItemUpdateFormData>({
    resolver: zodResolver(mode === 'create' ? itemCreateSchema : itemUpdateSchema),
    defaultValues: mode === 'create'
      ? {
          title: '',
          description: '',
        }
      : {
          title: item?.title || '',
          description: item?.description || '',
        },
  });

  const onSubmit = async (data: ItemCreateFormData | ItemUpdateFormData) => {
    try {
      if (mode === 'create') {
        await createMutation.mutateAsync(data as ItemCreateFormData);
        toast.success('Item created successfully');
        router.push('/dashboard/items');
      } else if (mode === 'update' && item) {
        await updateMutation.mutateAsync({ itemId: item.id, data });
        toast.success('Item updated successfully');
        router.push('/dashboard/items');
      }
    } catch (error) {
      toast.error(mode === 'create' ? 'Failed to create item' : 'Failed to update item');
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>{mode === 'create' ? 'Create New Item' : 'Edit Item'}</CardTitle>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="title"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Title</FormLabel>
                  <FormControl>
                    <Input placeholder="Enter item title" {...field} value={field.value || ''} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description</FormLabel>
                  <FormControl>
                    <Textarea 
                      placeholder="Enter item description (optional)" 
                      {...field} 
                      value={field.value || ''} 
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <div className="flex gap-4">
              <Button 
                type="button" 
                variant="outline" 
                onClick={() => router.push('/dashboard/items')}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isLoading}>
                {isLoading 
                  ? (mode === 'create' ? 'Creating...' : 'Updating...') 
                  : (mode === 'create' ? 'Create Item' : 'Update Item')
                }
              </Button>
            </div>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}

// Keep the old exports for backward compatibility
export function ItemCreateForm({ 
  onSubmit, 
  isLoading 
}: { 
  onSubmit: (data: ItemCreateFormData) => void; 
  isLoading?: boolean;
}) {
  const form = useForm<ItemCreateFormData>({
    resolver: zodResolver(itemCreateSchema),
    defaultValues: {
      title: '',
      description: '',
    },
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Create New Item</CardTitle>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="title"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Title</FormLabel>
                  <FormControl>
                    <Input placeholder="Enter item title" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description</FormLabel>
                  <FormControl>
                    <Textarea 
                      placeholder="Enter item description (optional)" 
                      {...field} 
                      value={field.value || ''} 
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <Button type="submit" disabled={isLoading} className="w-full">
              {isLoading ? 'Creating...' : 'Create Item'}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}

export function ItemUpdateForm({ 
  item, 
  onSubmit, 
  isLoading 
}: { 
  item: ItemPublic;
  onSubmit: (data: ItemUpdateFormData) => void; 
  isLoading?: boolean;
}) {
  const form = useForm<ItemUpdateFormData>({
    resolver: zodResolver(itemUpdateSchema),
    defaultValues: {
      title: item.title,
      description: item.description,
    },
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Edit Item</CardTitle>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="title"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Title</FormLabel>
                  <FormControl>
                    <Input {...field} value={field.value || ''} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description</FormLabel>
                  <FormControl>
                    <Textarea {...field} value={field.value || ''} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <Button type="submit" disabled={isLoading} className="w-full">
              {isLoading ? 'Updating...' : 'Update Item'}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
