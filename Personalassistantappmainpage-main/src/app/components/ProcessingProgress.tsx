import { useState, useEffect } from 'react';
import { Check, Loader2 } from 'lucide-react';

interface ProcessingStep {
    id: string;
    label: string;
    status: 'pending' | 'processing' | 'complete';
}

interface ProcessingProgressProps {
    isVisible: boolean;
    meetingTitle: string;
    onComplete?: () => void;
}

export function ProcessingProgress({ isVisible, meetingTitle, onComplete }: ProcessingProgressProps) {
    const [steps, setSteps] = useState<ProcessingStep[]>([
        { id: 'transcribing', label: 'Transcribing', status: 'pending' },
        { id: 'speaker_memory', label: 'Speaker memory', status: 'pending' },
        { id: 'summary', label: 'Summary', status: 'pending' },
        { id: 'tasks', label: 'Tasks', status: 'pending' },
    ]);
    const [estimatedTime, setEstimatedTime] = useState('~5 more minutes');

    useEffect(() => {
        if (isVisible) {
            // Simulate progress through steps
            simulateProgress();
        }
    }, [isVisible]);

    const simulateProgress = async () => {
        // In real implementation, this would be driven by WebSocket events from the backend
        const stepDelays = [2000, 3000, 4000, 3000]; // Simulated delays for each step

        for (let i = 0; i < steps.length; i++) {
            // Set current step to processing
            setSteps(prev => prev.map((step, idx) => ({
                ...step,
                status: idx === i ? 'processing' : idx < i ? 'complete' : 'pending'
            })));

            // Update estimated time
            const remaining = steps.length - i;
            setEstimatedTime(`~${remaining} more minute${remaining > 1 ? 's' : ''}`);

            await new Promise(resolve => setTimeout(resolve, stepDelays[i]));
        }

        // Mark all complete
        setSteps(prev => prev.map(step => ({ ...step, status: 'complete' })));
        setEstimatedTime('Complete!');

        // Notify parent
        setTimeout(() => {
            onComplete?.();
        }, 1000);
    };

    if (!isVisible) return null;

    return (
        <div className="bg-[#242424] rounded-xl border border-white/10 p-6 my-6">
            <div className="flex items-center justify-between mb-6">
                <h3 className="text-white font-medium">Creating summary and transcript</h3>
                <span className="text-sm text-gray-400">It will take {estimatedTime}</span>
            </div>

            <div className="space-y-3">
                {steps.map((step) => (
                    <div key={step.id} className="flex items-center gap-3">
                        <div className="w-5 h-5 flex items-center justify-center">
                            {step.status === 'complete' ? (
                                <div className="w-5 h-5 bg-purple-600 rounded-full flex items-center justify-center">
                                    <Check className="w-3 h-3 text-white" />
                                </div>
                            ) : step.status === 'processing' ? (
                                <Loader2 className="w-5 h-5 text-purple-400 animate-spin" />
                            ) : (
                                <div className="w-5 h-5 border-2 border-gray-600 rounded-full" />
                            )}
                        </div>
                        <span className={`text-sm ${step.status === 'complete'
                                ? 'text-white'
                                : step.status === 'processing'
                                    ? 'text-purple-400'
                                    : 'text-gray-500'
                            }`}>
                            {step.label}
                        </span>
                    </div>
                ))}
            </div>
        </div>
    );
}
