'use client';

import React, { useState } from 'react';
import { useProcesses } from '@/context/ProcessContext';
import { ProcessType } from '@/lib/types/processes';
import { getProcessName } from '@/lib/workflows';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from "@/hooks/use-toast";

export function ProcessStartForm({ onSuccess }: { onSuccess?: () => void }) {
    const { toast } = useToast();
    const { startProcess } = useProcesses();
    const [selectedType, setSelectedType] = useState<ProcessType>(ProcessType.DECORATIONS);

    // Generic form state container
    const [formData, setFormData] = useState<Record<string, any>>({});

    const handleStart = () => {
        try {
            startProcess(selectedType, formData as any);
            toast({
                title: 'Process Started',
                description: `Successfully initiated ${getProcessName(selectedType)} process.`,
            });
            setFormData({});
            if (onSuccess) onSuccess();
        } catch (e) {
            toast({
                title: 'Error',
                description: 'Failed to start process.',
                variant: 'destructive',
            });
        }
    };

    const updateField = (field: string, value: any) => {
        setFormData((prev) => ({ ...prev, [field]: value }));
    };

    return (
        <Card className="w-full max-w-2xl bg-gradient-to-br from-white to-gray-50 dark:from-gray-950 dark:to-gray-900 border-none shadow-xl">
            <CardHeader>
                <CardTitle className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-purple-600">Start New Request</CardTitle>
                <CardDescription>Select a process type and fill in the initial details.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
                <div className="space-y-2">
                    <Label>Process Type</Label>
                    <Select
                        value={selectedType}
                        onValueChange={(v) => {
                            setSelectedType(v as ProcessType);
                            setFormData({}); // Reset form on type switch
                        }}
                    >
                        <SelectTrigger>
                            <SelectValue placeholder="Select type..." />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value={ProcessType.DECORATIONS}>Decorations and Medals</SelectItem>
                            <SelectItem value={ProcessType.LEAVE_REQUEST}>Leave Request</SelectItem>
                            <SelectItem value={ProcessType.EMPLOYMENT_CONDITIONS}>Change of Employment Conditions</SelectItem>
                        </SelectContent>
                    </Select>
                </div>

                {/* --- DECORATIONS FORM --- */}
                {selectedType === ProcessType.DECORATIONS && (
                    <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Employee Name</Label>
                                <Input placeholder="e.g. Peter VRSci" onChange={(e) => updateField('employeeName', e.target.value)} />
                            </div>
                            <div className="space-y-2">
                                <Label>Organizational Unit</Label>
                                <Input placeholder="e.g. Science Dept" onChange={(e) => updateField('organizationalUnit', e.target.value)} />
                            </div>
                        </div>
                        <div className="space-y-2">
                            <Label>Decoration Type</Label>
                            <Input placeholder="e.g. Gold Medal" onChange={(e) => updateField('decorationType', e.target.value)} />
                        </div>
                        <div className="space-y-2">
                            <Label>Justification</Label>
                            <Textarea placeholder="Reason for award..." onChange={(e) => updateField('justification', e.target.value)} />
                        </div>
                    </div>
                )}

                {/* --- LEAVE REQUEST FORM --- */}
                {selectedType === ProcessType.LEAVE_REQUEST && (
                    <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Employee Name</Label>
                                <Input placeholder="e.g. Alice Academic" onChange={(e) => updateField('employeeName', e.target.value)} />
                            </div>
                            <div className="space-y-2">
                                <Label>Position</Label>
                                <Input placeholder="e.g. Professor" onChange={(e) => updateField('employeePosition', e.target.value)} />
                            </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Leave Type</Label>
                                <Select onValueChange={(v) => updateField('leaveType', v)}>
                                    <SelectTrigger>
                                        <SelectValue placeholder="Select..." />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="Recreational">Recreational</SelectItem>
                                        <SelectItem value="Childcare">Childcare</SelectItem>
                                        <SelectItem value="Special">Special Circumstance</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="space-y-2">
                                <Label>Duration (Days)</Label>
                                <Input type="number" onChange={(e) => updateField('leaveDurationDays', parseInt(e.target.value))} />
                            </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Start Date</Label>
                                <Input type="date" onChange={(e) => updateField('leaveStartDate', e.target.value)} />
                            </div>
                            <div className="space-y-2">
                                <Label>End Date</Label>
                                <Input type="date" onChange={(e) => updateField('leaveEndDate', e.target.value)} />
                            </div>
                        </div>
                    </div>
                )}

                {/* --- EMPLOYMENT CONDITIONS FORM --- */}
                {selectedType === ProcessType.EMPLOYMENT_CONDITIONS && (
                    <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
                        <div className="space-y-2">
                            <Label>Employee Name</Label>
                            <Input placeholder="e.g. Alice Academic" onChange={(e) => updateField('employeeName', e.target.value)} />
                        </div>
                        <div className="space-y-2">
                            <Label>Proposed Conditions</Label>
                            <Textarea placeholder="Description of new role/salary..." onChange={(e) => updateField('proposedConditions', e.target.value)} />
                        </div>
                        <div className="space-y-2">
                            <Label>Justification</Label>
                            <Textarea placeholder="Reason for change..." onChange={(e) => updateField('changeJustification', e.target.value)} />
                        </div>
                        <div className="space-y-2">
                            <Label>Effective Date</Label>
                            <Input type="date" onChange={(e) => updateField('changeEffectiveDate', e.target.value)} />
                        </div>
                    </div>
                )}

                <Button
                    className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 transition-all duration-300 transform hover:scale-[1.02]"
                    onClick={handleStart}
                >
                    🚀 Submit Request
                </Button>
            </CardContent>
        </Card>
    );
}
