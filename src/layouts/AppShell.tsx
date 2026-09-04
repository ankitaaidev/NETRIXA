import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Flame,
  AlertTriangle,
  History,
  Building2,
  Bell,
  FileText,
  Settings,
  ChevronLeft,
  ChevronRight,
  Search,
  Activity,
  Database,
  Cpu,
  Globe,
  Menu,
} from "lucide-react";
import { useAppStore } from "../store";

const NAV = [
  { to: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { to: "/events", label: "Thermal Events", icon: Flame },
  { to: "/priority", label: "Priority Center", icon: AlertTriangle },
  { to: "/history", label: "Historical Intel", icon: History },
  { to: "/facilities", label: "Facilities", icon: Building2 },
  { to: "/alerts", label: "Alerts", icon: Bell },
  { to: "/reports", label: "Reports", icon: FileText },
];

const STATUS = [
  { label: "DATA PIPELINE", status: "ONLINE" },
  { label: "GIS ENGINE", status: "ONLINE" },
  { label: "AI ENGINE", status: "ONLINE" },
  { label: "DATABASE", status: "ONLINE" },
  { label: "SATELLITE FEED", status: "DEMO" },
];

export default function AppShell() {
  const { sidebarCollapsed, toggleSidebar, filters, setFilter } = useAppStore();
  const navigate = useNavigate();
  const [searchVal, setSearchVal] = useState("");

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setFilter("search", searchVal);
    navigate("/events");
  };

  return (
    <div className="flex h-full bg-[#050a14] overflow-hidden">
      {/* Sidebar */}
      <aside
        className={`flex flex-col flex-shrink-0 border-r border-[#1e3a5f] bg-[#050a14] transition-all duration-200 z-30 ${sidebarCollapsed ? "w-14" : "w-56"}`}
      >
        {/* Logo */}
        <div className="flex items-center gap-2 px-3 py-4 border-b border-[#1e3a5f] h-14 flex-shrink-0">
          {!sidebarCollapsed && (
            <>
              <div className="flex items-center justify-center w-7 h-7 bg-cyan-500/10 border border-cyan-500/30 flex-shrink-0">
                <Flame size={14} className="text-cyan-400" />
              </div>
              <div>
                <div className="font-display font-700 text-[17px] tracking-[0.15em] text-[#e2eaf5] leading-none">
                  NETRIXA
                </div>
                <div className="font-mono-data text-[8px] text-[#3d6490] tracking-[0.2em] mt-0.5">
                  THERMAL INTEL
                </div>
              </div>
            </>
          )}
          {sidebarCollapsed && (
            <div className="flex items-center justify-center w-7 h-7 bg-cyan-500/10 border border-cyan-500/30 mx-auto">
              <Flame size={14} className="text-cyan-400" />
            </div>
          )}
        </div>

        {/* Nav */}
        <nav className="flex-1 py-3 px-2 space-y-0.5 overflow-y-auto">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `nav-item ${isActive ? "active" : ""} ${sidebarCollapsed ? "justify-center px-0" : ""}`
              }
              title={sidebarCollapsed ? label : undefined}
            >
              <Icon size={15} className="flex-shrink-0" />
              {!sidebarCollapsed && <span>{label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* System status */}
        {!sidebarCollapsed && (
          <div className="px-3 py-3 border-t border-[#1e3a5f] space-y-1">
            <div className="font-mono-data text-[9px] text-[#3d6490] tracking-[0.15em] mb-2">
              SYSTEM STATUS
            </div>
            {STATUS.map(({ label, status }) => (
              <div key={label} className="flex items-center justify-between">
                <span className="font-mono-data text-[9px] text-[#3d6490]">
                  {label}
                </span>
                <span
                  className={`font-mono-data text-[9px] flex items-center gap-1 ${status === "ONLINE" ? "text-green-400" : "text-amber-400"}`}
                >
                  <span
                    className={`w-1.5 h-1.5 rounded-full ${status === "ONLINE" ? "bg-green-400" : "bg-amber-400"}`}
                  />
                  {status}
                </span>
              </div>
            ))}
            <div className="mt-2 pt-2 border-t border-[#122035]">
              <div className="font-mono-data text-[9px] text-[#3d6490]">
                LAST SYNC
              </div>
              <div className="font-mono-data text-[9px] text-[#7a9cc4]">
                2026-09-04 · 03:50 UTC
              </div>
            </div>
          </div>
        )}

        {/* Bottom */}
        <div
          className={`border-t border-[#1e3a5f] p-2 flex ${sidebarCollapsed ? "justify-center" : "items-center justify-between"}`}
        >
          {!sidebarCollapsed && (
            <NavLink
              to="/settings"
              className={({ isActive }) =>
                `nav-item flex-1 ${isActive ? "active" : ""}`
              }
            >
              <Settings size={14} />
              <span>Settings</span>
            </NavLink>
          )}
          <button
            onClick={toggleSidebar}
            className="p-1.5 text-[#3d6490] hover:text-[#7a9cc4] transition-colors"
          >
            {sidebarCollapsed ? (
              <ChevronRight size={14} />
            ) : (
              <ChevronLeft size={14} />
            )}
          </button>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Topbar */}
        <header className="flex items-center gap-3 px-4 h-14 border-b border-[#1e3a5f] bg-[#050a14] flex-shrink-0 z-20">
          {/* Demo banner */}
          <div className="hidden lg:flex items-center gap-1.5 border border-amber-800/40 bg-amber-950/20 px-2 py-1 rounded-sm">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
            <span className="font-mono-data text-[9px] text-amber-400 tracking-widest">
              DEMO ENVIRONMENT
            </span>
          </div>

          {/* Search */}
          <form onSubmit={handleSearch} className="flex-1 max-w-sm relative">
            <Search
              size={13}
              className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[#3d6490]"
            />
            <input
              type="text"
              value={searchVal}
              onChange={(e) => setSearchVal(e.target.value)}
              placeholder="Search events, facilities, states..."
              className="w-full bg-[#0a1628] border border-[#1e3a5f] text-[#e2eaf5] placeholder-[#3d6490] text-xs pl-8 pr-3 py-1.5 rounded-sm font-mono-data focus:outline-none focus:border-cyan-500/50"
            />
          </form>

          <div className="ml-auto flex items-center gap-4">
            {/* Data status */}
            <div className="hidden md:flex items-center gap-2">
              <Activity size={12} className="text-green-400" />
              <span className="font-mono-data text-[10px] text-[#7a9cc4]">
                12,482 EVENTS
              </span>
            </div>
            <div className="hidden md:flex items-center gap-2">
              <Database size={12} className="text-cyan-400" />
              <span className="font-mono-data text-[10px] text-[#7a9cc4]">
                INDIA · 2026
              </span>
            </div>

            {/* Notifications */}
            <NavLink
              to="/alerts"
              className="relative p-1.5 text-[#7a9cc4] hover:text-[#e2eaf5] transition-colors"
            >
              <Bell size={16} />
              <span className="absolute top-0 right-0 w-2 h-2 bg-red-500 rounded-full border border-[#050a14]" />
            </NavLink>

            {/* Operator */}
            <div className="flex items-center gap-2 pl-3 border-l border-[#1e3a5f]">
              <div className="w-7 h-7 bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center">
                <span className="font-mono-data text-[10px] text-cyan-400">
                  OP
                </span>
              </div>
              {!sidebarCollapsed && (
                <div className="hidden lg:block">
                  <div className="font-display font-600 text-xs text-[#e2eaf5] tracking-wide">
                    OPERATOR 01
                  </div>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Page */}
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
