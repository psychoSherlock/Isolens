"use client";

import { useEffect, useState } from "react";
import {
  IoCheckmarkCircleOutline,
  IoCloseCircleOutline,
  IoServerOutline,
  IoSettingsOutline,
} from "react-icons/io5";
import { getVersion, ping, getVMInfo } from "@/lib/api";

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="settings-detail">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export default function SettingsPage() {
  const [gatewayVersion, setGatewayVersion] = useState("Unavailable");
  const [gatewayReachable, setGatewayReachable] = useState(false);
  const [vmName, setVMName] = useState("WindowsSandbox");
  const [vmOS, setVMOS] = useState("Unavailable");
  const [vmMemory, setVMMemory] = useState("Unavailable");

  useEffect(() => {
    let active = true;
    void (async () => {
      const [versionResult, pingResult, vmResult] = await Promise.allSettled([
        getVersion(),
        ping(),
        getVMInfo("WindowsSandbox", true),
      ]);
      if (!active) return;

      if (versionResult.status === "fulfilled" && versionResult.value.data) {
        const data = versionResult.value.data as { version: string };
        setGatewayVersion(data.version || "Unavailable");
      }
      setGatewayReachable(
        pingResult.status === "fulfilled" && pingResult.value.status === "ok",
      );
      if (vmResult.status === "fulfilled" && vmResult.value.data) {
        const data = vmResult.value.data as { info: Record<string, string> };
        setVMName(data.info.name || "WindowsSandbox");
        setVMOS(data.info.ostype || "Unavailable");
        setVMMemory(data.info.memory ? `${data.info.memory} MB` : "Unavailable");
      }
    })();
    return () => { active = false; };
  }, []);

  return (
    <div className="settings-page max-w-5xl">
      <header className="page-intro mb-8">
        <h1>Settings</h1>
        <p className="mt-2 text-sm text-slate-600">
          Current configuration reported by the sandbox and gateway.
        </p>
      </header>

      <div className="settings-overview">
        <section className="settings-panel">
          <div className="settings-panel-heading">
            <span className="settings-icon"><IoServerOutline aria-hidden="true" /></span>
            <div>
              <h2>Sandbox machine</h2>
              <p>Windows analysis environment</p>
            </div>
          </div>
          <div className="settings-panel-details">
            <Detail label="Machine name" value={vmName} />
            <Detail label="Operating system" value={vmOS} />
            <Detail label="Memory" value={vmMemory} />
            <Detail label="Shared folder" value="SandboxShare" />
          </div>
        </section>

        <section className="settings-panel">
          <div className="settings-panel-heading">
            <span className="settings-icon"><IoSettingsOutline aria-hidden="true" /></span>
            <div>
              <h2>Analysis gateway</h2>
              <p>Local API service</p>
            </div>
            <span className={`settings-connection ${gatewayReachable ? "is-online" : "is-offline"}`}>
              {gatewayReachable ? <IoCheckmarkCircleOutline aria-hidden="true" /> : <IoCloseCircleOutline aria-hidden="true" />}
              {gatewayReachable ? "Connected" : "Unreachable"}
            </span>
          </div>
          <div className="settings-panel-details">
            <Detail label="Version" value={gatewayVersion} />
            <Detail label="API port" value="6969" />
            <Detail label="Connection" value={gatewayReachable ? "Available" : "Unavailable"} />
          </div>
        </section>
      </div>
    </div>
  );
}
