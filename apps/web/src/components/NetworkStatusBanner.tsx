import React from "react";
import { useNetworkStatus } from "../hooks/useNetworkStatus";

export const NetworkStatusBanner: React.FC = () => {
  const { isOnline, wasOffline } = useNetworkStatus();

  if (isOnline && !wasOffline) {
    return null;
  }

  if (!isOnline) {
    return (
      <aside
        aria-live="assertive"
        className="bg-amber-600/90 text-amber-50 px-4 py-2 text-xs flex items-center justify-between shadow-md border-b border-amber-500/30 backdrop-blur-sm transition-all"
      >
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-amber-200 animate-pulse" />
          <span className="font-medium">
            Offline Mode: Operating with cached knowledge base. Some remote syntheses may be delayed.
          </span>
        </div>
      </aside>
    );
  }

  return (
    <aside
      aria-live="polite"
      className="bg-emerald-600/90 text-emerald-50 px-4 py-1.5 text-xs flex items-center justify-between shadow-sm border-b border-emerald-500/30 backdrop-blur-sm transition-all"
    >
      <div className="flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-emerald-300" />
        <span className="font-medium">Connection restored. Live reasoning engine synchronized.</span>
      </div>
    </aside>
  );
};
