"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { BarChart3 } from "lucide-react"
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"

const items = [
  {
    title: "Analytics",
    url: "/dashboard",
    icon: BarChart3,
  },
]

export function AppSidebar() {
  const pathname = usePathname()

  return (
    <Sidebar variant="inset">
      <SidebarHeader className="pb-2">
        <Link href="/" className="flex items-center gap-1.5 px-2 py-1.5 cursor-pointer">
          <div className="font-medium" style={{ fontFamily: 'Helvetica Neue, Helvetica, Arial, sans-serif', fontSize: '16px', lineHeight: '24px', color: '#0A0A0A' }}>
            .-.
          </div>
          <span className="font-medium" style={{ fontFamily: 'Helvetica Neue, Helvetica, Arial, sans-serif', fontSize: '16px', lineHeight: '24px', color: '#0A0A0A' }}>
            Outstack
          </span>
        </Link>
      </SidebarHeader>
      <SidebarContent className="pt-0">
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {items.map((item) => {
                const Icon = item.icon
                return (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton
                      asChild
                      isActive={pathname === item.url}
                    >
                      <Link href={item.url}>
                        {Icon && <Icon className="!size-4" />}
                        <span>{item.title}</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                )
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  )
}

