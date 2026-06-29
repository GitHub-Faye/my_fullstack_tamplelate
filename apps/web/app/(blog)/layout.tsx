import { BlogLayout } from "@/features/blog/client";

export default function BlogRootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <BlogLayout>{children}</BlogLayout>;
}