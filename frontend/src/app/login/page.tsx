"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/Button";
import { Input } from "@/components/Input";
import { AuthLayout } from "@/components/AuthLayout";
import { useAuth, isApiError } from "@/lib/auth";
import { useToast } from "@/components/Toast";

const DEMO = { email: "demo@demo.com", password: "demo1234" };

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const toast = useToast();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
      router.replace("/dashboard");
    } catch (err) {
      toast.error(isApiError(err) ? err.message : "Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  function fillDemo() {
    setEmail(DEMO.email);
    setPassword(DEMO.password);
  }

  return (
    <AuthLayout title="Welcome back" subtitle="Log in to continue your prep.">
      <form onSubmit={submit} className="flex flex-col gap-4">
        <Input
          label="Email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
        />
        <Input
          label="Password"
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
        />
        <Button type="submit" size="lg" loading={loading} className="mt-1 w-full">
          Log in
        </Button>
        <Button type="button" variant="secondary" className="w-full" onClick={fillDemo}>
          Use demo account
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-muted">
        No account?{" "}
        <Link href="/register" className="text-accent hover:underline">
          Create one
        </Link>
      </p>
    </AuthLayout>
  );
}
