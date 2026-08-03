import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary text-primary-foreground hover:bg-primary/80",
        secondary:
          "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
        destructive:
          "border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80",
        outline: "text-foreground",
        // 明细色阶 —— 用于任务状态/类型区分，可同时适配浅色/深色主题
        success:
          "border-transparent bg-emerald-100 text-emerald-800 hover:bg-emerald-100/80 dark:bg-emerald-900/40 dark:text-emerald-300 dark:hover:bg-emerald-900/50",
        warning:
          "border-transparent bg-amber-100 text-amber-800 hover:bg-amber-100/80 dark:bg-amber-900/40 dark:text-amber-300 dark:hover:bg-amber-900/50",
        danger:
          "border-transparent bg-rose-100 text-rose-700 hover:bg-rose-100/80 dark:bg-rose-900/40 dark:text-rose-300 dark:hover:bg-rose-900/50",
        info:
          "border-transparent bg-sky-100 text-sky-800 hover:bg-sky-100/80 dark:bg-sky-900/40 dark:text-sky-300 dark:hover:bg-sky-900/50",
        violet:
          "border-transparent bg-violet-100 text-violet-800 hover:bg-violet-100/80 dark:bg-violet-900/40 dark:text-violet-300 dark:hover:bg-violet-900/50",
        cyan:
          "border-transparent bg-cyan-100 text-cyan-800 hover:bg-cyan-100/80 dark:bg-cyan-900/40 dark:text-cyan-300 dark:hover:bg-cyan-900/50",
        teal:
          "border-transparent bg-teal-100 text-teal-800 hover:bg-teal-100/80 dark:bg-teal-900/40 dark:text-teal-300 dark:hover:bg-teal-900/50",
        gray:
          "border-transparent bg-muted text-muted-foreground hover:bg-muted/80",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
