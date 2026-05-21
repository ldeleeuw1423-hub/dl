"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Button } from "@/components/ui/Button";
import { api, getErrorMessage } from "@/lib/api";
import { Zap } from "lucide-react";
import toast from "react-hot-toast";

interface RegisterForm {
  email: string;
  password: string;
  confirmPassword: string;
  name: string;
  role: string;
  organization: string;
}

const roleOptions = [
  { value: "engineer", label: "Engineer" },
  { value: "pm", label: "Projectmanager (PM)" },
  { value: "om", label: "Omgevingsmanager (OM)" },
  { value: "admin", label: "Beheerder" },
];

export default function RegisterPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<RegisterForm>({
    defaultValues: { role: "engineer" },
  });

  const password = watch("password");

  const onSubmit = async (data: RegisterForm) => {
    setLoading(true);
    try {
      await api.register({
        email: data.email,
        password: data.password,
        name: data.name,
        role: data.role,
        organization: data.organization || undefined,
      });
      toast.success("Account aangemaakt — je kunt nu inloggen");
      router.push("/login");
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-navy-950 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 bg-amber-500 rounded-xl flex items-center justify-center mb-3">
            <Zap className="h-6 w-6 text-white" />
          </div>
          <h1 className="text-xl font-bold text-white">InfraEstimator</h1>
          <p className="text-sm text-navy-400 mt-1">Account aanmaken</p>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-2xl">
          <h2 className="text-sm font-semibold text-gray-800 mb-5">Nieuw account</h2>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <Input
                label="Volledige naam"
                required
                error={errors.name?.message}
                className="col-span-2"
                {...register("name", { required: "Naam is verplicht" })}
              />
            </div>

            <Input
              label="E-mailadres"
              type="email"
              required
              error={errors.email?.message}
              {...register("email", {
                required: "E-mail is verplicht",
                pattern: {
                  value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                  message: "Ongeldig e-mailadres",
                },
              })}
            />

            <div className="grid grid-cols-2 gap-3">
              <Select
                label="Rol"
                required
                options={roleOptions}
                {...register("role", { required: true })}
              />
              <Input
                label="Organisatie"
                placeholder="bijv. Liander"
                {...register("organization")}
              />
            </div>

            <Input
              label="Wachtwoord"
              type="password"
              required
              error={errors.password?.message}
              hint="Minimaal 8 tekens"
              {...register("password", {
                required: "Wachtwoord is verplicht",
                minLength: { value: 8, message: "Minimaal 8 tekens vereist" },
              })}
            />

            <Input
              label="Herhaal wachtwoord"
              type="password"
              required
              error={errors.confirmPassword?.message}
              {...register("confirmPassword", {
                required: "Bevestig wachtwoord",
                validate: (v) => v === password || "Wachtwoorden komen niet overeen",
              })}
            />

            <Button type="submit" loading={loading} className="w-full mt-1">
              Account aanmaken
            </Button>
          </form>

          <p className="text-center text-xs text-gray-500 mt-4">
            Al een account?{" "}
            <a href="/login" className="text-navy-700 hover:underline font-medium">
              Aanmelden
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
