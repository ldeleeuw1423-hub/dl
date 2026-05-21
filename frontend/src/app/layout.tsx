import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Toaster } from "react-hot-toast";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: {
    default: "InfraEstimator — Netbeheer NL",
    template: "%s | InfraEstimator",
  },
  description:
    "Professioneel projectramingssysteem voor ondergrondse infrastructuur (gas & elektra netbeheer)",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="nl" className={inter.variable}>
      <body className="font-sans antialiased bg-gray-50 text-gray-900">
        {children}
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              fontSize: "13px",
              maxWidth: "400px",
              borderRadius: "8px",
            },
            success: {
              duration: 3000,
            },
            error: {
              duration: 5000,
            },
          }}
        />
      </body>
    </html>
  );
}
