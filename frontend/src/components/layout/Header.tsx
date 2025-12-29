"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { RoleToggle } from "./RoleToggle";

interface HeaderProps {
  title?: string;
  showBack?: boolean;
  status?: "Draft" | "Active" | "Archived";
}

export function Header({ title, showBack, status }: HeaderProps) {
  const pathname = usePathname();
  const isHome = pathname === "/";

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center">
        <div className="flex items-center gap-4">
          {showBack && (
            <Link href="/">
              <Button variant="ghost" size="sm">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="m15 18-6-6 6-6" />
                </svg>
                Back
              </Button>
            </Link>
          )}
          <Link href="/" className="flex items-center gap-2">
            <span className="text-xl">🦀</span>
            <span className="font-semibold">CRABGRASS</span>
          </Link>
          {title && (
            <>
              <span className="text-muted-foreground">/</span>
              <span className="font-medium">{title}</span>
              {status && (
                <Badge
                  variant={
                    status === "Active"
                      ? "default"
                      : status === "Draft"
                        ? "secondary"
                        : "outline"
                  }
                >
                  {status}
                </Badge>
              )}
            </>
          )}
        </div>
        <div className="ml-auto flex items-center gap-4">
          <RoleToggle />
        </div>
      </div>
    </header>
  );
}
