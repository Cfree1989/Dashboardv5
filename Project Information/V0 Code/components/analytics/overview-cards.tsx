import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { FileText, Clock, HardDrive, XCircle } from 'lucide-react'
import type { OverviewData } from "@/types/analytics"

interface OverviewCardsProps {
  data: OverviewData
}

export function OverviewCards({ data }: OverviewCardsProps) {
  const storagePercentage = (data.storageUsed / data.storageLimit) * 100

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Submissions</CardTitle>
          <FileText className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{data.totalSubmissions}</div>
          <p className="text-xs text-muted-foreground">
            All time submissions
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">In Queue</CardTitle>
          <Clock className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {Object.values(data.inQueueByStatus).reduce((a, b) => a + b, 0)}
          </div>
          <p className="text-xs text-muted-foreground">
            Jobs awaiting completion
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Avg Turnaround</CardTitle>
          <Clock className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{data.averageTurnaround}h</div>
          <p className="text-xs text-muted-foreground">
            From submission to completion
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Storage Usage</CardTitle>
          <HardDrive className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{storagePercentage.toFixed(1)}%</div>
          <p className="text-xs text-muted-foreground">
            {data.storageUsed.toFixed(1)} GB / {data.storageLimit} GB
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
