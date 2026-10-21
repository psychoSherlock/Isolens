"use client";

import { useEffect, useState } from "react";
import { vmScreenURL } from "@/lib/api";

type ScreenshotState = "connecting" | "live" | "stale";

/** Fetch live frames sequentially, keeping the last valid frame visible on errors. */
export function useLiveVMScreenshot(enabled: boolean, vm: string) {
  const [src, setSrc] = useState("");
  const [status, setStatus] = useState<ScreenshotState>("connecting");
  const [updatedAt, setUpdatedAt] = useState<number | null>(null);

  useEffect(() => {
    if (!enabled) {
      setSrc("");
      setStatus("connecting");
      setUpdatedAt(null);
      return;
    }

    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let activeUrl = "";
    const revokeTimers: ReturnType<typeof setTimeout>[] = [];
    const controllerRef: { current: AbortController | null } = { current: null };
    setStatus("connecting");

    const fetchFrame = async () => {
      const controller = new AbortController();
      controllerRef.current = controller;
      const timeout = setTimeout(() => controller.abort(), 10_000);
      try {
        const response = await fetch(vmScreenURL(vm), {
          cache: "no-store",
          signal: controller.signal,
        });
        if (!response.ok) throw new Error(`Screenshot request failed (${response.status})`);
        const blob = await response.blob();
        if (!blob.type.startsWith("image/")) throw new Error("Gateway did not return an image");
        const nextUrl = URL.createObjectURL(blob);
        try {
          const probe = new Image();
          probe.src = nextUrl;
          await probe.decode();
        } catch {
          URL.revokeObjectURL(nextUrl);
          throw new Error("Gateway returned an unreadable screenshot");
        }
        if (cancelled) {
          URL.revokeObjectURL(nextUrl);
          return;
        }
        const previousUrl = activeUrl;
        activeUrl = nextUrl;
        setSrc(nextUrl);
        setStatus("live");
        setUpdatedAt(Date.now());
        if (previousUrl) {
          revokeTimers.push(setTimeout(() => URL.revokeObjectURL(previousUrl), 1500));
        }
      } catch {
        if (!cancelled) setStatus("stale");
      } finally {
        clearTimeout(timeout);
        if (!cancelled) timer = setTimeout(fetchFrame, 2000);
      }
    };

    void fetchFrame();

    return () => {
      cancelled = true;
      controllerRef.current?.abort();
      if (timer) clearTimeout(timer);
      revokeTimers.forEach(clearTimeout);
      if (activeUrl) URL.revokeObjectURL(activeUrl);
    };
  }, [enabled, vm]);

  return { src, status, updatedAt };
}
