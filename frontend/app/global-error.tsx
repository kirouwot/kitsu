"use client";

import { useEffect } from "react";
import Link from "next/link";
import { ROUTES } from "@/constants/routes";
import { Button } from "@/components/ui/button";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <html>
      <body className="min-h-screen bg-[#0b0b0f] text-white">
        <div className="flex min-h-screen flex-col items-center justify-center gap-4 px-6 text-center">
          <h2 className="text-2xl font-semibold">Something went wrong</h2>
          <p className="max-w-md text-sm text-slate-300">
            An unexpected error occurred. You can try again or return to the
            homepage.
          </p>
          <div className="flex gap-3">
            <Button onClick={reset}>Try again</Button>
            <Button variant="secondary" asChild>
              <Link href={ROUTES.HOME}>Go home</Link>
            </Button>
          </div>
        </div>
      </body>
    </html>
  );
}
