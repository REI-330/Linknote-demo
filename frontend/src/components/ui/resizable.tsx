import type { ComponentProps } from "react";

import * as ResizablePrimitive from "react-resizable-panels";

function cn(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(" ");
}

type ResizablePanelGroupProps = Omit<ComponentProps<typeof ResizablePrimitive.Group>, "orientation"> & {
  direction?: "horizontal" | "vertical";
};

function ResizablePanelGroup({
  className,
  direction = "horizontal",
  ...props
}: ResizablePanelGroupProps) {
  return <ResizablePrimitive.Group orientation={direction} className={cn("bn-resizable-root", className)} {...props} />;
}

const ResizablePanel = ResizablePrimitive.Panel;

function ResizableHandle({
  className,
  ...props
}: ComponentProps<typeof ResizablePrimitive.Separator>) {
  return <ResizablePrimitive.Separator className={cn("bn-layout-handle", className)} {...props} />;
}

export { ResizableHandle, ResizablePanel, ResizablePanelGroup };
