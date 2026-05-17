import React from "react";
import { cn } from "./utils";

export function Card({ children, className = "", as: Component = "div", interactive = false, ...props }) {
  return (
    <Component
      className={cn(
        "rounded-3xl border border-white/10 bg-white/[0.045] shadow-2xl shadow-black/20 backdrop-blur-xl",
        interactive && "transition duration-200 hover:-translate-y-0.5 hover:border-cyan-400/30 hover:bg-white/[0.07]",
        className
      )}
      {...props}
    >
      {children}
    </Component>
  );
}
