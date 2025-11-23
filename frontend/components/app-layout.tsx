"use client"

import { usePathname } from "next/navigation"
import { AppSidebar } from "@/components/app-sidebar"
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar"

export function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  
  // Determine header title based on route
  const getHeaderTitle = () => {
    if (pathname === "/dashboard") return "Analytics"
    return ""
  }

  const headerTitle = getHeaderTitle()

  return (
    <SidebarProvider
      style={
        {
          "--sidebar-width": "calc(var(--spacing) * 72)",
          "--header-height": "calc(var(--spacing) * 12)",
        } as React.CSSProperties
      }
    >
      <AppSidebar />
      <SidebarInset>
        <header 
          className="flex shrink-0 items-center gap-3 border-b px-4 py-3"
          style={{ height: "var(--header-height)" }}
        >
          <SidebarTrigger className="-ml-1" />
          {headerTitle && (
            <>
              <div className="w-px h-5 bg-border" />
              <h1 className="text-base font-medium">{headerTitle}</h1>
            </>
          )}
        </header>
        <div className="flex flex-1 flex-col">
          <div className="flex flex-1 flex-col gap-4 px-4 pb-4 pt-6">
            {children}
          </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}

