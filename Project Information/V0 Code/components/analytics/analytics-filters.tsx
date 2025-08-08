"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import type { AnalyticsFilters } from "@/types/analytics"

interface AnalyticsFiltersProps {
  filters: AnalyticsFilters
  onFiltersChange: (filters: AnalyticsFilters) => void
}

export function AnalyticsFilters({ filters, onFiltersChange }: AnalyticsFiltersProps) {
  const periodOptions = [
    { value: 7, label: "Last 7 days" },
    { value: 30, label: "Last 30 days" },
    { value: 90, label: "Last 90 days" },
  ]

  const disciplineOptions = [
    { value: "all", label: "All Disciplines" },
    { value: "architecture", label: "Architecture" },
    { value: "engineering", label: "Engineering" },
    { value: "art", label: "Art" },
    { value: "design", label: "Design" },
  ]

  const printerOptions = [
    { value: "all", label: "All Printers" },
    { value: "prusa-mk4s", label: "Prusa MK4S" },
    { value: "prusa-xl", label: "Prusa XL" },
    { value: "formlabs-form3", label: "Formlabs Form 3" },
  ]

  return (
    <Card className="mb-6">
      <CardContent className="pt-6">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium">Period:</span>
            <div className="flex space-x-1">
              {periodOptions.map((option) => (
                <Button
                  key={option.value}
                  variant={filters.period === option.value ? "default" : "outline"}
                  size="sm"
                  onClick={() => onFiltersChange({ ...filters, period: option.value as 7 | 30 | 90 })}
                >
                  {option.label}
                </Button>
              ))}
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium">Discipline:</span>
            <Select
              value={filters.discipline}
              onValueChange={(value) => onFiltersChange({ ...filters, discipline: value })}
            >
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {disciplineOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium">Printer:</span>
            <Select
              value={filters.printer}
              onValueChange={(value) => onFiltersChange({ ...filters, printer: value })}
            >
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {printerOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
