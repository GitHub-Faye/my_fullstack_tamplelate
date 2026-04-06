'use client';

import { useParams, useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  readItemV1ItemsItemsIdGet,
  updateItemV1ItemsItemsIdPut,
} from '@repo/sdk';
import type { ItemPublic, ItemUpdate } from '@repo/sdk';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

const formSchema = z.object({
  title: z.string().min(1, 'Title is required'),
  description: z.string().optional(),
});

type ItemFormValues = z.infer<typeof formSchema>;

export default function EditItemPage() {
  const { id } = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const itemId = id as string;

  const { data: item, isLoading } = useQuery({
    queryKey: ['item', itemId],
    queryFn: async () => {
      const response = await readItemV1ItemsItemsIdGet({
        path: { id: itemId },
      });
      return response.data as ItemPublic;
    },
  });

  const updateMutation = useMutation({
    mutationFn: async (values: ItemUpdate) => {
      const response = await updateItemV1ItemsItemsIdPut({
        body: values,
        path: { id: itemId },
      });
      return response.data;
    },
    onSuccess: () => {
      toast.success('Item updated successfully');
      queryClient.invalidateQueries({ queryKey: ['item', itemId] });
      queryClient.invalidateQueries({ queryKey: ['items'] });
      router.push('/dashboard/items');
    },
    onError: (error) => {
      toast.error('Failed to update item');
      console.error('Failed to update item:', error);
    },
  });

  const form = useForm<ItemFormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      title: '',
      description: '',
    },
  });

  useEffect(() => {
    if (item) {
      form.reset({
        title: item.title,
        description: item.description || '',
      });
    }
  }, [item, form]);

  function onSubmit(values: ItemFormValues) {
    const updateData: ItemUpdate = {
      title: values.title,
      description: values.description || null,
    };
    updateMutation.mutate(updateData);
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="container max-w-4xl py-6">
      <Card>
        <CardHeader>
          <CardTitle>Edit Item</CardTitle>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
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

              <div className="flex justify-end space-x-4">
                <Button type="button" variant="outline" onClick={() => router.back()}>
                  Cancel
                </Button>
                <Button type="submit" disabled={updateMutation.isPending}>
                  {updateMutation.isPending ? 'Updating...' : 'Update Item'}
                </Button>
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  );
}
