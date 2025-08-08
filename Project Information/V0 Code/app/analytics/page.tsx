"use client"

import { useState, useEffect } from "react"
import { OverviewCards } from "@/components/analytics/overview-cards"
import { TrendCharts } from "@/components/analytics/trend-charts"
import { ResourceMetrics } from "@/components/analytics/resource-metrics"
import { FinancialSummary } from "@/components/analytics/financial-summary"
import { AnalyticsFilters } from "@/components/analytics/analytics-filters"
import { fetchAnalyticsData } from "@/lib/analytics-api"
import type { AnalyticsData, AnalyticsFilters as FilterType } from "@/types/analytics"

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [lastRefreshed, setLastRefreshed] = useState<Date | null>(null)
  const [filters, setFilters] = useState<FilterType>({
    period: 30,
    discipline: "all",
    printer: "all",
  })

  const loadData = async () => {
    try {
      setLoading(true)
      const analyticsData = await fetchAnalyticsData(filters)
      setData(analyticsData)
      setLastRefreshed(new Date())
    } catch (error) {
      console.error("Error loading analytics data:", error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [filters])

  const handleFiltersChange = (newFilters: FilterType) => {
    setFilters(newFilters)
  }

  const handleRefresh = () => {
    loadData()
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col md:flex-row md:items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-4 md:mb-0">Analytics Dashboard</h1>
          <div className="flex items-center space-x-4">
            {lastRefreshed && (
              <span className="text-sm text-gray-500">
                Last updated: {lastRefreshed.toLocaleTimeString()}
              </span>
            )}
            <button
              onClick={() => window.location.href = '/dashboard'}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
            >
              Dashboard
            </button>
            <button
              onClick={() => window.location.href = '/admin'}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              Admin
            </button>
            <button
              onClick={handleRefresh}
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              {loading ? "Loading..." : "Refresh"}
            </button>
            <button
              onClick={() => {
                if (typeof window !== "undefined") {
                  localStorage.removeItem("staffLoggedIn")
                  window.location.href = "/login"
                }
              }}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Logout
            </button>
          </div>
        </div>

        <AnalyticsFilters filters={filters} onFiltersChange={handleFiltersChange} />

        {loading && !data ? (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="bg-white rounded-xl p-6 animate-pulse">
                  <div className="h-4 bg-gray-200 rounded mb-2"></div>
                  <div className="h-8 bg-gray-200 rounded"></div>
                </div>
              ))}
            </div>
            <div className="bg-white rounded-xl p-6 animate-pulse">
              <div className="h-64 bg-gray-200 rounded"></div>
            </div>
          </div>
        ) : data ? (
          <div className="space-y-6">
            <OverviewCards data={data.overview} />
            <TrendCharts data={data.trends} />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ResourceMetrics data={data.resources} />
              <FinancialSummary data={data.financial} />
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-xl p-8 text-center">
            <p className="text-gray-500">Failed to load analytics data. Please try refreshing.</p>
          </div>
        )}
      </div>
    </div>
  )
}
