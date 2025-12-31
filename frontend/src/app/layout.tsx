import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Crabgrass",
  description: "Idea-to-innovation platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-background antialiased">
        {children}
      </body>
    </html>
  );
}
