"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { api, getErrorMessage } from "@/lib/api";
import { setAuthToken } from "@/lib/auth";
import { Zap, Lock } from "lucide-react";
import toast from "react-hot-toast";

interface LoginForm {
  email: string;
  password: string;
}

export default function LoginPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>();

  const onSubmit = async (data: LoginForm) => {
    setLoading(true);
    try {
      const result = await api.login(data.email, data.password);
      setAuthToken(result.access_token, result.user);
      toast.success(`Welkom terug, ${result.user.name}`);
      router.push("/dashboard");
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-navy-950 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 bg-amber-500 rounded-xl flex items-center justify-center mb-3 shadow-lg">
            <Zap className="h-6 w-6 text-white" />
          </div>
          <h1 className="text-xl font-bold text-white">InfraEstimator</h1>
          <p className="text-sm text-navy-400 mt-1">Netbeheer Projectraming NL</p>
        </div>

        {/* Form */}
        <div className="bg-white rounded-xl p-6 shadow-2xl">
          <div className="flex items-center gap-2 mb-6">
            <Lock className="h-4 w-4 text-navy-600" />
            <h2 className="text-sm font-semibold text-gray-800">Aanmelden</h2>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <Input
              label="E-mailadres"
              type="email"
              placeholder="naam@bedrijf.nl"
              autoComplete="email"
              required
              error={errors.email?.message}
              {...register("email", {
                required: "E-mailadres is verplicht",
                pattern: {
                  value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                  message: "Ongeldig e-mailadres",
                },
              })}
            />
            <Input
              label="Wachtwoord"
              type="password"
              autoComplete="current-password"
              required
              error={errors.password?.message}
              {...register("password", { required: "Wachtwoord is verplicht" })}
            />
            <Button type="submit" loading={loading} className="w-full">
              Aanmelden
            </Button>
          </form>

          <p className="text-center text-xs text-gray-500 mt-4">
            Nog geen account?{" "}
            <a href="/register" className="text-navy-700 hover:underline font-medium">
              Registreren
            </a>
          </p>
        </div>

        <p className="text-center text-xs text-navy-600 mt-6">
          &copy; {new Date().getFullYear()} InfraEstimator — Alleen voor geautoriseerde gebruikers
        </p>
      </div>
    </div>
  );
}
