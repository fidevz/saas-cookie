import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function ProtectedNotFound() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center px-4 text-center py-16">
      <p className="text-sm font-medium uppercase tracking-widest text-muted-foreground">
        404
      </p>
      <h1 className="mt-4 text-3xl font-bold tracking-tight">Page not found</h1>
      <p className="mt-3 text-base text-muted-foreground max-w-sm">
        The page you are looking for does not exist or has been moved.
      </p>
      <div className="mt-8">
        <Button asChild>
          <Link href="/dashboard">Go to Dashboard</Link>
        </Button>
      </div>
    </div>
  );
}
