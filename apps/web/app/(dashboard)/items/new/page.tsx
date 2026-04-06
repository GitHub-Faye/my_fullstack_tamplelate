'use client';

import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { createItemV1ItemsItemsPost } from '@repo/sdk';
import type { ItemCreate } from '@repo/sdk';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

const formSchema = z.object({
  title: z.string().min(1, 'Title is required'),
  description: z.string().optional(),
});

type ItemFormValues = z.infer<typeof formSchema>;

export default function NewItemPage() {
  const router = useRouter();
  const queryClient = useQueryClient();

  const createMutation = useMutation({
    mutationFn: async (values: ItemCreate) => {
      const response = await createItemV1ItemsItemsPost({
        body: values
      });
      return response.data;
    },
    onSuccess: () => {
      toast.success('Item created successfully');
      queryClient.invalidateQueries({ queryKey: ['items'] });
      router.push('/dashboard/items');
    },
    onError: (error) => {
      toast.error('Failed to create item');
      console.error('Failed to create item:', error);
    }
  });

  const form = useForm<ItemFormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      title: '',
      description: '',
    },
  });

  async function onSubmit(values: ItemFormValues) {
    const itemData: ItemCreate = {
      title: values.title,
      description: values.description || null,
    };
    createMutation.mutate(itemData);
  }

  return (
    <div className="container max-w-4xl py-6">
      <Card>
        <CardHeader>
          <CardTitle>Create New Item</CardTitle>
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
                <Button type="submit" disabled={createMutation.isPending}>
                  {createMutation.isPending ? 'Creating...' : 'Create Item'}
                </Button>
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  );
}
