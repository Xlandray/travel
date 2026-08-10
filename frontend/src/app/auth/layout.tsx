import Link from "next/link";
import Logo from "@/components/Logo";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-canvas-token flex flex-col justify-center py-12 sm:px-6 lg:px-8 font-sans text-main-token">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <Link href="/" className="flex justify-center">
          <Logo className="h-14" />
        </Link>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="card-token py-8 px-4 sm:px-10">
          {children}
        </div>
      </div>
    </div>
  );
}
