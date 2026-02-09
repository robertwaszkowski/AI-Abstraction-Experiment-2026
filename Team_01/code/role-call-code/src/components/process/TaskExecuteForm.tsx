'use client';

import React, { useState } from 'react';
import { useProcesses } from '@/context/ProcessContext';
import { ProcessInstance, ProcessStep, AnyProcessData, ProcessStatus } from '@/lib/types/processes';
import { getProcessName, getStepName } from '@/lib/workflows';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { CheckCircle2, XCircle, FileText, User } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

export function TaskExecuteForm({ process, onClose }: { process: ProcessInstance; onClose: () => void }) {
    const { toast } = useToast();
    const { completeTask } = useProcesses();
    const [formData, setFormData] = useState<Record<string, any>>({});

    const handleAction = (actionType: string) => {
        // Merge simplistic actions into the form data
        // Ideally this would be more complex and validated
        completeTask(process.id, { ...formData } as any);
        toast({ title: 'Task Completed', description: 'Moved to next step.' });
        onClose();
    };

    const updateField = (field: string, value: any) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    // Helper to render read-only data
    const renderDataRow = (label: string, value: any) => (
        <div className="flex justify-between py-2 border-b border-gray-100 dark:border-gray-800 last:border-0">
            <span className="text-gray-500 font-medium">{label}</span>
            <span className="text-gray-900 dark:text-gray-100 font-semibold">{String(value || '-')}</span>
        </div>
    );

    const getStatusVariant = (status: ProcessStatus) => {
        switch (status) {
            case ProcessStatus.ACTIVE: return 'default';
            case ProcessStatus.COMPLETED: return 'success'; // Ensure 'success' variant exists or fallback to secondary/green style if custom
            case ProcessStatus.REJECTED: return 'destructive';
            case ProcessStatus.CANCELLED: return 'destructive';
            default: return 'secondary';
        }
    };

    return (
        <Card className="w-full border-2 border-blue-50 dark:border-blue-900/30 shadow-lg">
            <CardHeader className="bg-gray-50 dark:bg-gray-900/50">
                <div className="flex justify-between items-center">
                    <CardTitle className="flex items-center gap-2">
                        <FileText className="w-5 h-5 text-blue-600" />
                        {getProcessName(process.type)}
                    </CardTitle>
                    <Badge variant={getStatusVariant(process.status)}>{process.status}</Badge>
                </div>
                <CardDescription>
                    Current Step: <span className="font-bold text-foreground">{getStepName(process.currentStep)}</span>
                </CardDescription>
            </CardHeader>

            <CardContent className="space-y-6 pt-6">
                {/* --- READ ONLY CONTEXT --- */}
                <div className="bg-white dark:bg-gray-950 rounded-lg p-4 border shadow-sm">
                    <h4 className="text-sm font-bold uppercase tracking-wider text-gray-400 mb-3">Request Details</h4>
                    {renderDataRow('Employee', (process.data as any).employeeName)}
                    {renderDataRow('Initiator', process.data.initiatorUsername)}

                    {/* Specific fields based on type */}
                    {'decorationType' in process.data && renderDataRow('Decoration', process.data.decorationType)}
                    {'leaveType' in process.data && renderDataRow('Leave Type', process.data.leaveType)}
                    {'leaveDurationDays' in process.data && renderDataRow('Days', process.data.leaveDurationDays)}

                    {/* Show decisions if available */}
                    {'finalDecision' in process.data && renderDataRow('Final Decision', (process.data as any).finalDecision)}
                </div>

                {/* --- INPUT FIELDS FOR CURRENT STEP --- */}
                <div className="space-y-4">
                    <h4 className="text-sm font-bold uppercase tracking-wider text-blue-600 mb-2">Required Actions</h4>

                    {/* -- DECORATIONS INPUTS -- */}
                    {process.currentStep === ProcessStep.DECORATIONS_PRK_REVIEW && (
                        <div className="space-y-2">
                            <Label>Reviewer Opinion</Label>
                            <Textarea placeholder="Support strongly..." onChange={e => updateField('reviewerOpinion', e.target.value)} />
                        </div>
                    )}
                    {process.currentStep === ProcessStep.DECORATIONS_RKR_DECISION && (
                        <div className="space-y-2">
                            <Label>Rector Decision</Label>
                            <Select onValueChange={v => updateField('rkrDecision', v)}>
                                <SelectTrigger><SelectValue placeholder="Decision..." /></SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="Accepted">Accept Application</SelectItem>
                                    <SelectItem value="Rejected">Reject Application</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    )}
                    {process.currentStep === ProcessStep.DECORATIONS_PD_REGISTER && (
                        <div className="space-y-2">
                            <Label>Award Grant Date</Label>
                            <Input type="date" onChange={e => updateField('awardGrantDate', e.target.value)} />
                        </div>
                    )}


                    {/* -- LEAVE INPUTS -- */}
                    {process.currentStep === ProcessStep.LEAVE_HEAD_OU_REVIEW && (
                        <div className="space-y-2">
                            <Label>Head of O.U. Decision</Label>
                            <Select onValueChange={v => updateField('headOuDecision', v)}>
                                <SelectTrigger><SelectValue placeholder="Decision..." /></SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="Approved">Approve</SelectItem>
                                    <SelectItem value="Rejected">Reject</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    )}
                    {process.currentStep === ProcessStep.LEAVE_PD_REVIEW && (
                        <div className="grid gap-4">
                            <div className="space-y-2">
                                <Label>Entitlement Check</Label>
                                <Select onValueChange={v => updateField('pdReviewStatus', v)}>
                                    <SelectTrigger><SelectValue placeholder="Status..." /></SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="Entitlement Confirmed">Confirmed</SelectItem>
                                        <SelectItem value="Entitlement Exceeded">Exceeded</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="space-y-2">
                                <Label>Is Academic Teacher?</Label>
                                <Select onValueChange={v => updateField('isAcademicTeacher', v === 'true')}>
                                    <SelectTrigger><SelectValue placeholder="Select..." /></SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="true">Yes</SelectItem>
                                        <SelectItem value="false">No</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>
                    )}
                    {(process.currentStep === ProcessStep.LEAVE_PRK_REVIEW) && (
                        <div className="space-y-2">
                            <Label>PRK Review Status</Label>
                            <Select onValueChange={v => updateField('prkReviewStatus', v)}>
                                <SelectTrigger><SelectValue placeholder="Decision..." /></SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="Approved">Approve</SelectItem>
                                    <SelectItem value="Rejected">Reject</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    )}
                    {(process.currentStep === ProcessStep.LEAVE_PRN_REVIEW) && (
                        <div className="space-y-2">
                            <Label>PRN Review Status</Label>
                            <Select onValueChange={v => updateField('prnReviewStatus', v)}>
                                <SelectTrigger><SelectValue placeholder="Decision..." /></SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="Approved">Approve</SelectItem>
                                    <SelectItem value="Rejected">Reject</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    )}
                    {(process.currentStep === ProcessStep.LEAVE_RKR_DECISION || process.currentStep === ProcessStep.LEAVE_KAN_DECISION) && (
                        <div className="space-y-2">
                            <Label>Final Decision</Label>
                            <Select onValueChange={v => updateField('finalDecision', v)}>
                                <SelectTrigger><SelectValue placeholder="Decision..." /></SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="Approved">Approve</SelectItem>
                                    <SelectItem value="Rejected">Reject</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    )}


                    {/* -- EMPLOYMENT INPUTS -- */}
                    {process.currentStep === ProcessStep.EMPLOYMENT_HEAD_OU_FORWARD && (
                        <div className="space-y-2">
                            <Label>Head of O.U. Review</Label>
                            <Select onValueChange={v => updateField('headOuReviewStatus', v)}>
                                <SelectTrigger><SelectValue placeholder="Decision..." /></SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="Approved">Approve</SelectItem>
                                    <SelectItem value="Rejected">Reject</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    )}
                    {process.currentStep === ProcessStep.EMPLOYMENT_PD_REVIEW && (
                        <div className="grid gap-4">
                            <div className="space-y-2">
                                <Label>PD Verification</Label>
                                <Select onValueChange={v => updateField('pdReviewStatus', v)}>
                                    <SelectTrigger><SelectValue placeholder="Status..." /></SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="Confirmed">Confirmed</SelectItem>
                                        <SelectItem value="Rejected">Rejected</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="space-y-2">
                                <Label>Is Academic Teacher?</Label>
                                <Select onValueChange={v => updateField('isAcademicTeacher', v === 'true')}>
                                    <SelectTrigger><SelectValue placeholder="Select..." /></SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="true">Yes</SelectItem>
                                        <SelectItem value="false">No</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>
                    )}
                    {process.currentStep === ProcessStep.EMPLOYMENT_KWE_REVIEW && (
                        <div className="space-y-2">
                            <Label>Quartermaster Financial Opinion</Label>
                            <Select onValueChange={v => updateField('kweFinancialOpinion', v)}>
                                <SelectTrigger><SelectValue placeholder="Opinion..." /></SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="Funds Available">Funds Available</SelectItem>
                                    <SelectItem value="No Funds">No Funds</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    )}
                    {(process.currentStep === ProcessStep.EMPLOYMENT_PRK_REVIEW) && (
                        <div className="space-y-2">
                            <Label>PRK Opinion</Label>
                            <Select onValueChange={v => updateField('prkOpinion', v)}>
                                <SelectTrigger><SelectValue placeholder="Decision..." /></SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="Approved">Approve</SelectItem>
                                    <SelectItem value="Rejected">Reject</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    )}
                    {(process.currentStep === ProcessStep.EMPLOYMENT_PRN_REVIEW) && (
                        <div className="space-y-2">
                            <Label>PRN Opinion</Label>
                            <Select onValueChange={v => updateField('prnOpinion', v)}>
                                <SelectTrigger><SelectValue placeholder="Decision..." /></SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="Approved">Approve</SelectItem>
                                    <SelectItem value="Rejected">Reject</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    )}
                    {(process.currentStep === ProcessStep.EMPLOYMENT_RKR_DECISION) && (
                        <div className="space-y-2">
                            <Label>Final Decision (RKR)</Label>
                            <Select onValueChange={v => updateField('finalDecision', v)}>
                                <SelectTrigger><SelectValue placeholder="Decision..." /></SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="Approved">Approve</SelectItem>
                                    <SelectItem value="Rejected">Reject</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    )}


                </div>
            </CardContent>
            <CardFooter>
                <Button className="w-full" onClick={() => handleAction('Complete')}>
                    <CheckCircle2 className="w-4 h-4 mr-2" />
                    Complete Task & Forward
                </Button>
            </CardFooter>
        </Card>
    );
}
