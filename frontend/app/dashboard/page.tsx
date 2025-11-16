"use client"

import { useEffect, useState } from "react"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { Info, RefreshCw, X, Loader2 } from "lucide-react"

interface CampaignData {
  campaign_id: string
  campaign_name: string
  companies_count: number
  people_count: number
  people_engaged: number
  open_rate: number
  reply_rate: number
  campaign_status: string
}

interface MailboxData {
  email: string
  status: string
  mailbox_id: string | null
  campaigns?: string[] | null
}

export default function DashboardPage() {
  const [campaigns, setCampaigns] = useState<CampaignData[]>([])
  const [mailboxes, setMailboxes] = useState<MailboxData[]>([])
  const [loading, setLoading] = useState(true)
  const [mailboxesLoading, setMailboxesLoading] = useState(true)
  const [refreshingCampaigns, setRefreshingCampaigns] = useState(false)
  const [refreshingMailboxes, setRefreshingMailboxes] = useState(false)
  const [mailboxesFetching, setMailboxesFetching] = useState(false) // Track if fetch is in progress
  const [error, setError] = useState<string | null>(null)
  const [selectedMailboxInfo, setSelectedMailboxInfo] = useState<{ email: string; campaigns: string[] } | null>(null)

  useEffect(() => {
    const loadData = async () => {
      // First load campaigns, then load mailboxes after campaigns are done
      // This prevents resource contention and rate limiting issues
      await fetchCampaigns()
      // Wait a bit to let the backend recover from campaigns processing
      await new Promise(resolve => setTimeout(resolve, 500))
      await fetchMailboxes()
    }
    loadData()
  }, [])

  const fetchCampaigns = async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshingCampaigns(true)
      } else {
        setLoading(true)
      }
      setError(null)
      const response = await fetch("http://localhost:8000/api/campaigns/dashboard", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      })
      
      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`Failed to fetch campaigns: ${response.status} ${response.statusText}. ${errorText}`)
      }
      
      const data = await response.json()
      setCampaigns(Array.isArray(data) ? data : [])
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "An error occurred"
      setError(errorMessage)
      console.error("Error fetching campaigns:", err)
    } finally {
      if (isRefresh) {
        setRefreshingCampaigns(false)
      } else {
        setLoading(false)
      }
    }
  }

  const fetchMailboxes = async (isRefresh = false) => {
    // Prevent multiple simultaneous fetches
    if (mailboxesFetching) {
      console.log("Mailboxes fetch already in progress, skipping...")
      return
    }
    
    try {
      setMailboxesFetching(true) // Mark as fetching immediately
      if (isRefresh) {
        setRefreshingMailboxes(true)
      } else {
        setMailboxesLoading(true)
      }
      const response = await fetch("http://localhost:8000/api/mailboxes", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      })
      
      if (!response.ok) {
        const errorText = await response.text()
        console.error(`Failed to fetch mailboxes: ${response.status} ${response.statusText}. ${errorText}`)
        setMailboxes([]) // Reset to empty array on error
        return
      }
      
      const data = await response.json()
      setMailboxes(Array.isArray(data) ? data : [])
    } catch (err) {
      console.error("Error fetching mailboxes:", err)
      setMailboxes([]) // Reset to empty array on exception
    } finally {
      setMailboxesFetching(false) // Clear fetching flag
      if (isRefresh) {
        setRefreshingMailboxes(false)
      } else {
        setMailboxesLoading(false)
      }
    }
  }

  const startLemwarm = async (mailboxId: string, email: string) => {
    if (!mailboxId) {
      alert("Mailbox ID is missing")
      return
    }

    try {
      const response = await fetch(`http://localhost:8000/api/mailboxes/${mailboxId}/start-lemwarm`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`Failed to start lemwarm: ${errorText}`)
      }

      // Refresh mailboxes to get updated status
      await fetchMailboxes(true)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "An error occurred"
      alert(`Error starting lemwarm for ${email}: ${errorMessage}`)
      console.error("Error starting lemwarm:", err)
    }
  }

  const stopLemwarm = async (mailboxId: string, email: string) => {
    if (!mailboxId) {
      alert("Mailbox ID is missing")
      return
    }

    try {
      const response = await fetch(`http://localhost:8000/api/mailboxes/${mailboxId}/stop-lemwarm`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`Failed to stop lemwarm: ${errorText}`)
      }

      // Refresh mailboxes to get updated status
      await fetchMailboxes(true)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "An error occurred"
      alert(`Error stopping lemwarm for ${email}: ${errorMessage}`)
      console.error("Error stopping lemwarm:", err)
    }
  }

  const setCampaignInactive = async (campaignId: string, campaignName: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/campaigns/${campaignId}/set-inactive`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`Failed to set campaign inactive: ${errorText}`)
      }

      // Refresh campaigns to get updated data
      await fetchCampaigns(true)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "An error occurred"
      alert(`Error setting campaign ${campaignName} inactive: ${errorMessage}`)
      console.error("Error setting campaign inactive:", err)
    }
  }

  return (
    <div className="container mx-auto py-12 px-4 max-w-7xl">

      {error && (
        <Card className="mb-8 border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <p className="text-sm text-red-700 mb-4">Error: {error}</p>
            <Button
              onClick={() => fetchCampaigns(true)}
              variant="outline"
              size="sm"
              className="border-red-300 text-red-700 hover:bg-red-100"
            >
              Retry
            </Button>
          </CardContent>
        </Card>
      )}

      <div className="mb-8 flex justify-between items-center">
        <h2 className="text-lg font-normal text-gray-800">Running Campaigns</h2>
        <Button
          onClick={() => fetchCampaigns(true)}
          disabled={loading || refreshingCampaigns}
          variant="outline"
          size="sm"
          className="h-8 px-2 text-xs"
        >
          {refreshingCampaigns ? (
            <>
              <Loader2 className="h-3 w-3 animate-spin" />
              Refreshing...
            </>
          ) : (
            <>
              <RefreshCw className="h-3 w-3" />
              Refresh
            </>
          )}
        </Button>
      </div>

      {loading ? null : (
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-gray-700">Campaign Name</TableHead>
                  <TableHead className="text-right text-gray-700">Companies</TableHead>
                  <TableHead className="text-right text-gray-700">People</TableHead>
                  <TableHead className="text-right text-gray-700">People Engaged</TableHead>
                  <TableHead className="text-right text-gray-700">Open Rate (%)</TableHead>
                  <TableHead className="text-right text-gray-700">Reply Rate (%)</TableHead>
                  {campaigns.some(c => c.campaign_status === "ended") && (
                    <TableHead className="text-right text-gray-700">Status</TableHead>
                  )}
                </TableRow>
                {campaigns.length > 0 && (
                  <TableRow className="h-8">
                    <TableCell className="text-xs text-gray-500 py-1">Total</TableCell>
                    <TableCell className="text-right text-xs text-gray-500 py-1">
                      <span className="inline-flex items-center px-2 py-0.5 text-xs font-normal text-gray-600 border border-gray-200 rounded-md bg-white">
                        {campaigns.reduce((sum, c) => sum + c.companies_count, 0).toLocaleString()}
                      </span>
                    </TableCell>
                    <TableCell className="text-right text-xs text-gray-500 py-1">
                      <span className="inline-flex items-center px-2 py-0.5 text-xs font-normal text-gray-600 border border-gray-200 rounded-md bg-white">
                        {campaigns.reduce((sum, c) => sum + c.people_count, 0).toLocaleString()}
                      </span>
                    </TableCell>
                    <TableCell className="text-right text-xs text-gray-500 py-1">
                      <span className="inline-flex items-center px-2 py-0.5 text-xs font-normal text-gray-600 border border-gray-200 rounded-md bg-white">
                        {campaigns.reduce((sum, c) => sum + c.people_engaged, 0).toLocaleString()}
                      </span>
                    </TableCell>
                    <TableCell className="text-right text-xs text-gray-500 py-1">
                      {(() => {
                        const campaignsWithOpenRate = campaigns.filter(c => c.open_rate > 0);
                        if (campaignsWithOpenRate.length > 0) {
                          const avgOpenRate = campaignsWithOpenRate.reduce((sum, c) => sum + c.open_rate, 0) / campaignsWithOpenRate.length;
                          return (
                            <span className="inline-flex items-center px-2 py-0.5 text-xs font-normal text-gray-600 border border-gray-200 rounded-md bg-white">
                              Ø {avgOpenRate.toFixed(2)}%
                            </span>
                          );
                        }
                        return "–";
                      })()}
                    </TableCell>
                    <TableCell className="text-right text-xs text-gray-500 py-1">
                      {campaigns.length > 0 ? (
                        <span className="inline-flex items-center px-2 py-0.5 text-xs font-normal text-gray-600 border border-gray-200 rounded-md bg-white">
                          Ø {(campaigns.reduce((sum, c) => sum + c.reply_rate, 0) / campaigns.length).toFixed(2)}%
                        </span>
                      ) : (
                        "–"
                      )}
                    </TableCell>
                    {campaigns.some(c => c.campaign_status === "ended") && (
                      <TableCell className="text-right text-xs text-gray-500 py-1"></TableCell>
                    )}
                  </TableRow>
                )}
              </TableHeader>
              <TableBody>
                {campaigns.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={campaigns.some(c => c.campaign_status === "ended") ? 7 : 6} className="text-center text-muted-foreground py-12">
                      No running campaigns found
                    </TableCell>
                  </TableRow>
                ) : (
                  campaigns.map((campaign) => (
                    <TableRow key={campaign.campaign_id}>
                      <TableCell className="font-normal text-gray-800">
                        {campaign.campaign_name}
                      </TableCell>
                      <TableCell className="text-right">
                        <span className="inline-flex items-center px-2 py-0.5 text-xs font-normal text-gray-700 border border-gray-200 rounded-md bg-white">
                          {campaign.companies_count.toLocaleString()}
                        </span>
                      </TableCell>
                      <TableCell className="text-right">
                        <span className="inline-flex items-center px-2 py-0.5 text-xs font-normal text-gray-700 border border-gray-200 rounded-md bg-white">
                          {campaign.people_count.toLocaleString()}
                        </span>
                      </TableCell>
                      <TableCell className="text-right">
                        <span className="inline-flex items-center px-2 py-0.5 text-xs font-normal text-gray-700 border border-gray-200 rounded-md bg-white">
                          {campaign.people_engaged.toLocaleString()}
                        </span>
                      </TableCell>
                      <TableCell className="text-right">
                        {campaign.open_rate === 0 ? (
                          "–"
                        ) : (
                          <span className="inline-flex items-center px-2 py-0.5 text-xs font-normal text-gray-700 border border-gray-200 rounded-md bg-white">
                            {campaign.open_rate.toFixed(2)}%
                          </span>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <span className="inline-flex items-center px-2 py-0.5 text-xs font-normal text-gray-700 border border-gray-200 rounded-md bg-white">
                          {campaign.reply_rate.toFixed(2)}%
                        </span>
                      </TableCell>
                      {campaigns.some(c => c.campaign_status === "ended") && (
                        <TableCell className="text-right">
                          {campaign.campaign_status === "ended" ? (
                            <Button
                              onClick={() => setCampaignInactive(campaign.campaign_id, campaign.campaign_name)}
                              variant="outline"
                              size="sm"
                            >
                              Set inactive
                            </Button>
                          ) : null}
                        </TableCell>
                      )}
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      <Separator className="my-12" />

      <div className="mb-8 flex justify-between items-center">
        <h2 className="text-lg font-normal text-gray-800">Sender Mailboxes</h2>
        <Button
          onClick={() => fetchMailboxes(true)}
          disabled={mailboxesLoading || refreshingMailboxes || mailboxesFetching}
          variant="outline"
          size="sm"
          className="h-8 px-2 text-xs"
        >
          {refreshingMailboxes ? (
            <>
              <Loader2 className="h-3 w-3 animate-spin" />
              Refreshing...
            </>
          ) : (
            <>
              <RefreshCw className="h-3 w-3" />
              Refresh
            </>
          )}
        </Button>
      </div>

      {mailboxesLoading ? null : (
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-gray-700">Email Address</TableHead>
                  <TableHead className="text-right text-gray-700">Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {mailboxes.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={2} className="text-center text-muted-foreground py-12">
                      No mailboxes found
                    </TableCell>
                  </TableRow>
                ) : (
                  mailboxes.map((mailbox) => (
                    <TableRow key={mailbox.email}>
                      <TableCell className="font-normal text-gray-800">
                        {mailbox.email}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          {mailbox.status === "stuck" && mailbox.mailbox_id ? (
                            <>
                              {mailbox.campaigns && mailbox.campaigns.length > 0 && (
                                <Button
                                  onClick={() => setSelectedMailboxInfo({ email: mailbox.email, campaigns: mailbox.campaigns! })}
                                  variant="ghost"
                                  size="icon"
                                  className="h-8 w-8"
                                  title="Show campaigns"
                                >
                                  <Info className="h-4 w-4" />
                                </Button>
                              )}
                              <Button
                                onClick={() => startLemwarm(mailbox.mailbox_id!, mailbox.email)}
                                variant="default"
                                size="sm"
                              >
                                Start Lemwarm
                              </Button>
                            </>
                          ) : mailbox.status === "conflict" && mailbox.mailbox_id ? (
                            <>
                              {mailbox.campaigns && mailbox.campaigns.length > 0 && (
                                <Button
                                  onClick={() => setSelectedMailboxInfo({ email: mailbox.email, campaigns: mailbox.campaigns! })}
                                  variant="ghost"
                                  size="icon"
                                  className="h-8 w-8"
                                  title="Show campaigns"
                                >
                                  <Info className="h-4 w-4" />
                                </Button>
                              )}
                              <Button
                                onClick={() => stopLemwarm(mailbox.mailbox_id!, mailbox.email)}
                                variant="outline"
                                size="sm"
                              >
                                Stop Lemwarm
                              </Button>
                            </>
                          ) : (
                            <span className="inline-flex items-center px-2 py-0.5 text-xs font-normal text-gray-700 border border-gray-200 rounded-md bg-white">
                              {mailbox.status}
                            </span>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Info Popup */}
      {selectedMailboxInfo && (
        <>
          <div
            className="fixed inset-0 bg-black/20 z-40"
            onClick={() => setSelectedMailboxInfo(null)}
          />
          <Card className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-50 min-w-[300px] max-w-[500px]">
            <CardHeader className="pb-4">
              <div className="flex justify-between items-start">
                <CardTitle className="text-sm font-normal text-gray-800">
                  Campaigns for {selectedMailboxInfo.email}
                </CardTitle>
                <Button
                  onClick={() => setSelectedMailboxInfo(null)}
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 -mt-1 -mr-1"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="max-h-60 overflow-y-auto">
                {selectedMailboxInfo.campaigns.length > 0 ? (
                  <ul className="space-y-1">
                    {selectedMailboxInfo.campaigns.map((campaign, index) => (
                      <li key={index} className="text-sm text-gray-700 py-2 px-3 hover:bg-gray-50 rounded-md">
                        {campaign}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-muted-foreground">No campaigns found</p>
                )}
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}

