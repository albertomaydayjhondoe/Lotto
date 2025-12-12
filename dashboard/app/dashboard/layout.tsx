"use client"

import React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { 
  LayoutDashboard, 
  List, 
  Settings, 
  TrendingUp, 
  Megaphone,
  LogOut,
  Menu,
  X,
  Sparkles,
  Lightbulb,
  Zap,
  Bell,
  History
} from "lucide-react"
import { useAuth } from "@/hooks/use-auth"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { useAlertStats } from "@/lib/alerts/hooks"
import { useAIHistoryCount } from "@/lib/ai_history/hooks"

const navigation = [
  { name: "Overview", href: "/dashboard", icon: LayoutDashboard },
  { name: "Queue", href: "/dashboard/queue", icon: List },
  { name: "Orchestrator", href: "/dashboard/orchestrator", icon: Settings },
  { name: "Platforms", href: "/dashboard/platforms", icon: TrendingUp },
  { name: "Campaigns", href: "/dashboard/campaigns", icon: Megaphone },
  { name: "Alerts", href: "/dashboard/alerts", icon: Bell },
]

const aiNavigation = [
  { name: "AI Overview", href: "/dashboard/ai", icon: Sparkles },
  { name: "Recommendations", href: "/dashboard/ai/recommendations", icon: Lightbulb },
  { name: "Actions", href: "/dashboard/ai/actions", icon: Zap },
  { name: "AI History", href: "/dashboard/ai/history", icon: History, showCount: true },
]

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()
  const { logout } = useAuth()
  const [sidebarOpen, setSidebarOpen] = React.useState(false)
  const { data: alertStats } = useAlertStats()
  const { data: historyCount } = useAIHistoryCount()

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-64 bg-white border-r transform transition-transform duration-200 ease-in-out lg:translate-x-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-between p-6 border-b">
            <Link href="/dashboard" className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-br from-purple-600 to-blue-600 rounded-lg" />
              <span className="text-xl font-bold">Stakazo</span>
            </Link>
            <button
              className="lg:hidden"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="h-6 w-6" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
            {/* Main Navigation */}
            <div className="space-y-1">
              {navigation.map((item) => {
                const isActive = pathname === item.href
                const isAlerts = item.name === "Alerts"
                const unreadCount = alertStats?.unread_count || 0
                
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={cn(
                      "flex items-center justify-between px-4 py-3 rounded-lg transition-colors",
                      isActive
                        ? "bg-primary text-primary-foreground"
                        : "text-gray-700 hover:bg-gray-100"
                    )}
                    onClick={() => setSidebarOpen(false)}
                  >
                    <div className="flex items-center space-x-3">
                      <item.icon className="h-5 w-5" />
                      <span className="font-medium">{item.name}</span>
                    </div>
                    {isAlerts && unreadCount > 0 && (
                      <Badge 
                        variant="destructive" 
                        className="h-5 min-w-[20px] flex items-center justify-center text-xs px-1.5"
                      >
                        {unreadCount > 99 ? '99+' : unreadCount}
                      </Badge>
                    )}
                  </Link>
                )
              })}
            </div>

            {/* AI Section */}
            <div className="pt-4 mt-4 border-t">
              <div className="px-4 mb-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                AI Intelligence
              </div>
              <div className="space-y-1">
                {aiNavigation.map((item) => {
                  const isActive = pathname === item.href
                  const showHistoryCount = item.showCount && historyCount && historyCount > 0
                  
                  return (
                    <Link
                      key={item.name}
                      href={item.href}
                      className={cn(
                        "flex items-center justify-between px-4 py-3 rounded-lg transition-colors",
                        isActive
                          ? "bg-gradient-to-r from-purple-600 to-pink-600 text-white"
                          : "text-gray-700 hover:bg-gradient-to-r hover:from-purple-50 hover:to-pink-50"
                      )}
                      onClick={() => setSidebarOpen(false)}
                    >
                      <div className="flex items-center space-x-3">
                        <item.icon className="h-5 w-5" />
                        <span className="font-medium">{item.name}</span>
                      </div>
                      {showHistoryCount && (
                        <Badge 
                          variant={isActive ? "secondary" : "outline"}
                          className="h-5 min-w-[20px] flex items-center justify-center text-xs px-1.5"
                        >
                          {historyCount}
                        </Badge>
                      )}
                    </Link>
                  )
                })}
              </div>
            </div>
          </nav>

          {/* Logout */}
          <div className="p-4 border-t">
            <Button
              variant="ghost"
              className="w-full justify-start"
              onClick={logout}
            >
              <LogOut className="h-5 w-5 mr-3" />
              Logout
            </Button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top header */}
        <header className="bg-white border-b sticky top-0 z-30">
          <div className="flex items-center justify-between px-6 py-4">
            <button
              className="lg:hidden"
              onClick={() => setSidebarOpen(true)}
            >
              <Menu className="h-6 w-6" />
            </button>
            <h1 className="text-2xl font-bold">Dashboard</h1>
            <div className="flex items-center space-x-4">
              <Link href="/dashboard/alerts" className="relative">
                <Bell className="h-6 w-6 text-gray-500 hover:text-gray-700 transition-colors" />
                {alertStats && alertStats.unread_count > 0 && (
                  <Badge 
                    variant="destructive" 
                    className="absolute -top-2 -right-2 h-5 min-w-[20px] flex items-center justify-center text-xs px-1.5"
                  >
                    {alertStats.unread_count > 99 ? '99+' : alertStats.unread_count}
                  </Badge>
                )}
              </Link>
              <span className="text-sm text-gray-500">Admin</span>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="p-6">
          {children}
        </main>
      </div>
    </div>
  )
}
