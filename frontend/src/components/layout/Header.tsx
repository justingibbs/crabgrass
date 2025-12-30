"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronLeft } from "lucide-react";
import { RoleToggle } from "./RoleToggle";
import { cn } from "@/lib/utils";

interface HeaderProps {
  title?: string;
  status?: "Draft" | "Active" | "Archived";
}

export function Header({ title, status }: HeaderProps) {
  const pathname = usePathname();
  const isHome = pathname === "/";

  return (
    <header className="border-b border-border bg-background">
      <div className="flex items-center justify-between px-4 py-3">
        <div className="flex items-center gap-3">
          {!isHome && (
            <Link
              href="/"
              className="flex items-center gap-1 text-muted-foreground hover:text-foreground transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
              Back
            </Link>
          )}
          <Link href="/" className="flex items-center gap-2 font-semibold">
            <span className="text-xl">🦀</span>
            <span>CRABGRASS</span>
          </Link>
          {title && (
            <>
              <span className="text-muted-foreground">›</span>
              <span>{title}</span>
            </>
          )}
          {status && (
            <StatusBadge status={status} />
          )}
        </div>
        <RoleToggle />
      </div>
    </header>
  );
}

function StatusBadge({ status }: { status: "Draft" | "Active" | "Archived" }) {
  return (
    <span
      className={cn(
        "px-2 py-0.5 text-xs rounded-full",
        status === "Draft" && "bg-yellow-100 text-yellow-800",
        status === "Active" && "bg-green-100 text-green-800",
        status === "Archived" && "bg-gray-100 text-gray-800"
      )}
    >
      {status}
    </span>
  );
}
