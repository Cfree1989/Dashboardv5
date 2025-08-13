"use client";

import * as React from "react";
import * as TooltipPrimitive from "@radix-ui/react-tooltip";

function cx(...classes: Array<string | false | null | undefined>) {
	return classes.filter(Boolean).join(" ");
}

type TooltipProviderProps = React.ComponentProps<typeof TooltipPrimitive.Provider>;

export function TooltipProvider({
	children,
	delayDuration = 200,
	skipDelayDuration = 0,
}: TooltipProviderProps) {
	return (
		<TooltipPrimitive.Provider
			delayDuration={delayDuration}
			skipDelayDuration={skipDelayDuration}
		>
			{children}
		</TooltipPrimitive.Provider>
	);
}

export const Tooltip = TooltipPrimitive.Root;
export const TooltipTrigger = TooltipPrimitive.Trigger;

export const TooltipContent = React.forwardRef<
	React.ElementRef<typeof TooltipPrimitive.Content>,
	React.ComponentPropsWithoutRef<typeof TooltipPrimitive.Content>
>(function TooltipContent({ className, side = "top", sideOffset = 6, ...props }, ref) {
	return (
		<TooltipPrimitive.Content
			ref={ref}
			side={side}
			sideOffset={sideOffset}
			className={cx(
				"z-50 rounded-md border bg-popover px-3 py-1.5 text-sm text-popover-foreground shadow-md",
				"motion-safe:transition-all motion-safe:duration-150",
				"motion-reduce:transition-none",
				className
			)}
			{...props}
		/>
	);
});


