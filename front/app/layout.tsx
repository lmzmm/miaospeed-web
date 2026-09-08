import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MiaoSpeed SpeedTest",
  description: "Clash / Mihomo 节点测速",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN" className="h-full antialiased">
      <body className="min-h-full">{children}</body>
    </html>
  );
}
