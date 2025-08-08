"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { UserPlus, UserCheck, UserX, Mail } from 'lucide-react'
import type { StaffMember } from "@/types/admin"

export function StaffManagement() {
  const [staff, setStaff] = useState<StaffMember[]>([])
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)
  const [newStaffName, setNewStaffName] = useState("")
  const [newStaffEmail, setNewStaffEmail] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    loadStaff()
  }, [])

  const loadStaff = async () => {
    try {
      // Mock data - replace with actual API call
      setStaff([
        {
          id: "1",
          name: "John Doe",
          email: "john.doe@university.edu",
          isActive: true,
          createdAt: "2023-09-01T10:00:00Z",
          lastLogin: "2023-09-15T14:30:00Z",
        },
        {
          id: "2",
          name: "Jane Smith",
          email: "jane.smith@university.edu",
          isActive: true,
          createdAt: "2023-08-15T09:00:00Z",
          lastLogin: "2023-09-14T16:45:00Z",
        },
        {
          id: "3",
          name: "Bob Wilson",
          email: "bob.wilson@university.edu",
          isActive: false,
          createdAt: "2023-07-01T11:00:00Z",
          lastLogin: "2023-08-30T12:15:00Z",
        },
      ])
    } catch (error) {
      console.error("Error loading staff:", error)
    }
  }

  const handleAddStaff = async () => {
    if (!newStaffName.trim() || !newStaffEmail.trim()) return

    try {
      setIsLoading(true)
      // API call to add staff member
      console.log("Adding staff:", { name: newStaffName, email: newStaffEmail })
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // Add to local state (in real app, refetch from server)
      const newStaff: StaffMember = {
        id: Date.now().toString(),
        name: newStaffName,
        email: newStaffEmail,
        isActive: true,
        createdAt: new Date().toISOString(),
        lastLogin: null,
      }
      
      setStaff([...staff, newStaff])
      setNewStaffName("")
      setNewStaffEmail("")
      setIsAddModalOpen(false)
    } catch (error) {
      console.error("Error adding staff:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleToggleActive = async (staffId: string, isActive: boolean) => {
    try {
      // API call to toggle staff status
      console.log("Toggling staff status:", { staffId, isActive })
      
      // Update local state
      setStaff(staff.map(member => 
        member.id === staffId ? { ...member, isActive } : member
      ))
    } catch (error) {
      console.error("Error toggling staff status:", error)
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Staff Members</CardTitle>
          <Button onClick={() => setIsAddModalOpen(true)}>
            <UserPlus className="w-4 h-4 mr-2" />
            Add Staff
          </Button>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {staff.map((member) => (
              <div
                key={member.id}
                className="flex items-center justify-between p-4 border border-gray-200 rounded-lg"
              >
                <div className="flex-1">
                  <div className="flex items-center space-x-3">
                    <h3 className="font-medium text-gray-900">{member.name}</h3>
                    <span
                      className={`px-2 py-1 text-xs font-semibold rounded-full ${
                        member.isActive
                          ? "bg-green-100 text-green-800"
                          : "bg-red-100 text-red-800"
                      }`}
                    >
                      {member.isActive ? "Active" : "Inactive"}
                    </span>
                  </div>
                  <div className="flex items-center text-sm text-gray-500 mt-1">
                    <Mail className="w-4 h-4 mr-1" />
                    {member.email}
                  </div>
                  <div className="text-xs text-gray-400 mt-1">
                    Last login: {member.lastLogin ? new Date(member.lastLogin).toLocaleString() : "Never"}
                  </div>
                </div>
                <div className="flex space-x-2">
                  {member.isActive ? (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleToggleActive(member.id, false)}
                    >
                      <UserX className="w-4 h-4 mr-1" />
                      Deactivate
                    </Button>
                  ) : (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleToggleActive(member.id, true)}
                    >
                      <UserCheck className="w-4 h-4 mr-1" />
                      Reactivate
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Dialog open={isAddModalOpen} onOpenChange={setIsAddModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add New Staff Member</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="staff-name">Full Name</Label>
              <Input
                id="staff-name"
                value={newStaffName}
                onChange={(e) => setNewStaffName(e.target.value)}
                placeholder="Enter staff member's full name"
              />
            </div>
            <div>
              <Label htmlFor="staff-email">Email Address</Label>
              <Input
                id="staff-email"
                type="email"
                value={newStaffEmail}
                onChange={(e) => setNewStaffEmail(e.target.value)}
                placeholder="Enter staff member's email"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsAddModalOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleAddStaff}
              disabled={!newStaffName.trim() || !newStaffEmail.trim() || isLoading}
            >
              {isLoading ? "Adding..." : "Add Staff"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
