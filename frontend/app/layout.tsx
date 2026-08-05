import type { Metadata } from "next";
import { Inter, Manrope } from "next/font/google";
import { AppShell } from "@/components/AppShell";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-body" });
const manrope = Manrope({ subsets: ["latin"], variable: "--font-display" });

export const metadata: Metadata = {
  title: {
    default: "Sentiment Analysis Tool",
    template: "%s | Sentiment Analysis Tool",
  },
  description: "A production sentiment analysis and classical ML research workspace.",
  applicationName: "Sentiment Analysis Tool",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.variable + " " + manrope.variable}>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
