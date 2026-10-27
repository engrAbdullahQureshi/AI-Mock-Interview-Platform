"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/Button";
import { Input } from "@/components/Input";
import { AuthLayout } from "@/components/AuthLayout";
import { useAuth, isApiError } from "@/lib/auth";
import { useToast } from "@/components/Toast";

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();
  const toast = useToast();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (password.length < 8) {
      toast.error("Password must be at least 8 characters.");
      return;
    }
    setLoading(true);
    try {
      await register(username, email, password);
      router.replace("/dashboard");
    } catch (err) {
      toast.error(isApiError(err) ? err.message : "Could not create account.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout title="Create your account" subtitle="Start practicing in under a minute.">
      <form onSubmit={submit} className="flex flex-col gap-4">
        <Input
          label="Username"
          required
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="abdullah"
        />
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
          autoComplete="new-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="At least 8 characters"
        />
        <Button type="submit" size="lg" loading={loading} className="mt-1 w-full">
          Create account
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-muted">
        Already have an account?{" "}
        <Link href="/login" className="text-accent hover:underline">
          Log in
        </Link>
      </p>
    </AuthLayout>
  );
}
