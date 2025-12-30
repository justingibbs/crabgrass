"use client";

import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

export type Role = "Frontline" | "Senior";

interface RoleToggleProps {
  className?: string;
}

export function RoleToggle({ className }: RoleToggleProps) {
  const [role, setRole] = useState<Role>("Frontline");

  // Load role from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem("crabgrass-role");
    if (stored === "Senior" || stored === "Frontline") {
      setRole(stored);
    }
  }, []);

  const handleToggle = (newRole: Role) => {
    setRole(newRole);
    localStorage.setItem("crabgrass-role", newRole);
    // Dispatch custom event for other components to listen
    window.dispatchEvent(new CustomEvent("role-change", { detail: newRole }));
  };

  return (
    <div className={cn("flex items-center gap-1 text-sm", className)}>
      <button
        onClick={() => handleToggle("Frontline")}
        className={cn(
          "px-2 py-1 rounded transition-colors",
          role === "Frontline"
            ? "bg-primary text-primary-foreground"
            : "text-muted-foreground hover:text-foreground"
        )}
      >
        {role === "Frontline" ? "◉" : "○"} Sarah
      </button>
      <span className="text-muted-foreground">│</span>
      <button
        onClick={() => handleToggle("Senior")}
        className={cn(
          "px-2 py-1 rounded transition-colors",
          role === "Senior"
            ? "bg-primary text-primary-foreground"
            : "text-muted-foreground hover:text-foreground"
        )}
      >
        {role === "Senior" ? "◉" : "○"} VP Sales
      </button>
    </div>
  );
}

// Hook to get current role
export function useRole(): Role {
  const [role, setRole] = useState<Role>("Frontline");

  useEffect(() => {
    const stored = localStorage.getItem("crabgrass-role");
    if (stored === "Senior" || stored === "Frontline") {
      setRole(stored);
    }

    const handleChange = (e: CustomEvent<Role>) => {
      setRole(e.detail);
    };

    window.addEventListener("role-change", handleChange as EventListener);
    return () => {
      window.removeEventListener("role-change", handleChange as EventListener);
    };
  }, []);

  return role;
}
