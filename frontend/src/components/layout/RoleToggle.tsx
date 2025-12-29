"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";

type Role = "Frontline" | "Senior";

const STORAGE_KEY = "crabgrass-role";

export function RoleToggle() {
  const [role, setRole] = useState<Role>("Frontline");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const stored = localStorage.getItem(STORAGE_KEY) as Role | null;
    if (stored === "Frontline" || stored === "Senior") {
      setRole(stored);
    }
  }, []);

  const toggleRole = () => {
    const newRole = role === "Frontline" ? "Senior" : "Frontline";
    setRole(newRole);
    localStorage.setItem(STORAGE_KEY, newRole);
  };

  if (!mounted) {
    return (
      <div className="flex items-center gap-2 text-sm">
        <span className="text-muted-foreground">Loading...</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 text-sm">
      <Button
        variant={role === "Frontline" ? "default" : "ghost"}
        size="sm"
        onClick={() => role !== "Frontline" && toggleRole()}
        className="h-8"
      >
        Sarah
      </Button>
      <Button
        variant={role === "Senior" ? "default" : "ghost"}
        size="sm"
        onClick={() => role !== "Senior" && toggleRole()}
        className="h-8"
      >
        VP Sales
      </Button>
    </div>
  );
}
