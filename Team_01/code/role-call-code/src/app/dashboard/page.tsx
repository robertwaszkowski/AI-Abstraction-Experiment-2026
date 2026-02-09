'use client';

import { useAuth } from '@/hooks/useAuth';
import { useProcesses } from '@/context/ProcessContext';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { ProcessStartForm } from '@/components/process/ProcessStartForm';
import { TaskExecuteForm } from '@/components/process/TaskExecuteForm';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Loader2, LogOut, CheckCircle } from 'lucide-react';
import { ProcessStatus } from '@/lib/types/processes';
import { getProcessName, getStepName } from '@/lib/workflows';

export default function DashboardPage() {
  const { user, logout, loading } = useAuth();
  const { processes } = useProcesses();
  const router = useRouter();
  const [selectedProcessId, setSelectedProcessId] = useState<string | null>(null);
  const [isTaskOpen, setIsTaskOpen] = useState(false);

  useEffect(() => {
    if (!loading && !user) {
      router.replace('/login');
    }
  }, [user, loading, router]);

  if (loading || !user) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  // --- FILTERING LOGIC ---
  const myTasks = processes.filter(p =>
    p.status === ProcessStatus.ACTIVE &&
    p.assignedRole === user.roleCode
  );

  const myRequests = processes.filter(p =>
    p.data.initiatorUsername === user.username
  );

  const openTask = (id: string) => {
    setSelectedProcessId(id);
    setIsTaskOpen(true);
  };

  const activeTaskProcess = processes.find(p => p.id === selectedProcessId);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <header className="sticky top-0 z-50 w-full border-b bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/60 dark:bg-gray-950/95 dark:border-gray-800">
        <div className="container flex h-14 items-center justify-between">
          <div className="flex items-center gap-2 font-bold text-xl ml-4">
            <span className="text-blue-600">Role</span>Call
          </div>
          <div className="flex items-center gap-4 mr-4">
            <div className="flex flex-col items-end">
              <span className="text-sm font-medium">{user.name}</span>
              <span className="text-xs text-muted-foreground">{user.role} ({user.roleCode})</span>
            </div>
            <Button variant="ghost" size="icon" onClick={logout}>
              <LogOut className="h-5 w-5" />
            </Button>
          </div>
        </div>
      </header>

      <main className="container py-6 space-y-8">
        <div className="grid gap-6 md:grid-cols-2">

          {/* --- LEFT COL: MY TASKS --- */}
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold tracking-tight">My Tasks</h2>
              <span className="bg-blue-100 text-blue-800 text-xs font-semibold px-2.5 py-0.5 rounded dark:bg-blue-200 dark:text-blue-800">
                {myTasks.length} Pending
              </span>
            </div>

            {myTasks.length === 0 ? (
              <Card className="border-dashed">
                <CardContent className="flex flex-col items-center justify-center p-6 text-center text-muted-foreground h-40">
                  <CheckCircle className="h-10 w-10 mb-2 opacity-20" />
                  <p>All caught up! No tasks assigned to your role.</p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-4">
                {myTasks.map(task => (
                  <Card key={task.id} className="hover:shadow-md transition-shadow cursor-pointer border-l-4 border-l-blue-500" onClick={() => openTask(task.id)}>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-base flex justify-between">
                        {getProcessName(task.type)}
                        <span className="text-xs font-normal text-muted-foreground">ID: {task.id}</span>
                      </CardTitle>
                      <CardDescription>{getStepName(task.currentStep || '')}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="text-sm">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">From:</span>
                          <span className="font-medium">{task.data.initiatorUsername}</span>
                        </div>
                        {/* Show key info preview */}
                        {'employeeName' in task.data && (
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Subject:</span>
                            <span className="font-medium">{(task.data as any).employeeName}</span>
                          </div>
                        )}
                      </div>
                    </CardContent>
                    <CardFooter className="pt-0 justify-end">
                      <Button size="sm" onClick={() => openTask(task.id)}>Execute Task</Button>
                    </CardFooter>
                  </Card>
                ))}
              </div>
            )}
          </div>


          {/* --- RIGHT COL: START NEW & HISTORY --- */}
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold tracking-tight">Start Process</h2>
            </div>
            <ProcessStartForm />

            <div className="mt-8">
              <h3 className="text-lg font-semibold mb-4 text-muted-foreground">My Active Requests</h3>
              <div className="space-y-3">
                {myRequests.map(req => (
                  <div key={req.id} className="flex items-center justify-between p-3 bg-white dark:bg-gray-950 rounded border text-sm">
                    <div>
                      <div className="font-medium">{getProcessName(req.type)}</div>
                      <div className="text-xs text-muted-foreground">Step: {req.currentStep ? getStepName(req.currentStep) : 'Completed'}</div>
                    </div>
                    <div className={`text-xs px-2 py-1 rounded ${req.status === 'COMPLETED' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>
                      {req.status}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* --- TASK MODAL --- */}
        <Dialog open={isTaskOpen} onOpenChange={setIsTaskOpen}>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Execute Task</DialogTitle>
            </DialogHeader>
            {activeTaskProcess && (
              <TaskExecuteForm
                process={activeTaskProcess}
                onClose={() => setIsTaskOpen(false)}
              />
            )}
          </DialogContent>
        </Dialog>

      </main>
    </div>
  );
}
