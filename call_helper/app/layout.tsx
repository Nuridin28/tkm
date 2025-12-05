import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Help Desk Казахтелеком",
  description: "Виртуальный помощник по услугам и поддержке Казахтелеком",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  );
}

