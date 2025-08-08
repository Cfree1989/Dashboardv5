"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import type { ResourceData } from "@/types/analytics"

interface ResourceMetricsProps {
  data: ResourceData
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444']

export function ResourceMetrics({ data }: ResourceMetricsProps) {
  // Prepare printer utilization data for stacked bar chart
  const utilizationData = data.printerUtilization[0]?.utilization.map((day, index) => {
    const result: any = { date: day.date }
    data.printerUtilization.forEach((printer, printerIndex) => {
      result[printer.printer] = printer.utilization[index]?.hours || 0
    })
    return result
  }) || []

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Printer Utilization</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={utilizationData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="date" 
                tickFormatter={(value) => new Date(value).toLocaleDateString()}
              />
              <YAxis />
              <Tooltip 
                labelFormatter={(value) => new Date(value).toLocaleDateString()}
                formatter={(value, name) => [`${value} hours`, name]}
              />
              {data.printerUtilization.map((printer, index) => (
                <Bar 
                  key={printer.printer}
                  dataKey={printer.printer} 
                  stackId="utilization"
                  fill={COLORS[index % COLORS.length]} 
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Material Consumption</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{data.materialConsumption.filament}g</div>
              <div className="text-sm text-gray-500">Filament Used</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{data.materialConsumption.resin}g</div>
              <div className="text-sm text-gray-500">Resin Used</div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Queue Age Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={data.queueAgeDistribution}
                cx="50%"
                cy="50%"
                outerRadius={80}
                fill="#8884d8"
                dataKey="count"
                label={({ ageRange, count }) => `${ageRange}: ${count}`}
              >
                {data.queueAgeDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}
