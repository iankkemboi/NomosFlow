import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NomosFlow — AI Dunning Engine",
  description: "AI-powered dunning and churn prevention for white-label energy retailers",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        {children}
      </body>
    </html>
  );
}
