import { useState, useEffect } from 'react';
import { Mic, Volume2, Radio, Check, X } from 'lucide-react';
import { getApiUrl, getApiHeaders } from '../config/api';

interface Device {
    id: string;
    name: string;
    available: boolean;
}

interface MicrophoneSelectorProps {
    isOpen: boolean;
    onClose: () => void;
    onSelect: (deviceId: string) => void;
}

export function MicrophoneSelector({ isOpen, onClose, onSelect }: MicrophoneSelectorProps) {
    const [devices, setDevices] = useState<Device[]>([]);
    const [selectedDevice, setSelectedDevice] = useState<string>('microphone');
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (isOpen) {
            fetchDevices();
        }
    }, [isOpen]);

    const fetchDevices = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const response = await fetch(getApiUrl('/api/devices'), {
                headers: getApiHeaders()
            });
            if (!response.ok) throw new Error('Failed to fetch devices');
            const data = await response.json();
            setDevices(data.devices || []);
            setSelectedDevice(data.default || 'microphone');
        } catch (err) {
            setError('Could not load audio devices');
            console.error('Error fetching devices:', err);
        } finally {
            setIsLoading(false);
        }
    };

    const handleConfirm = () => {
        onSelect(selectedDevice);
        onClose();
    };

    const getDeviceIcon = (deviceId: string) => {
        switch (deviceId) {
            case 'microphone':
                return <Mic className="w-5 h-5" />;
            case 'system':
                return <Volume2 className="w-5 h-5" />;
            case 'hybrid':
                return <Radio className="w-5 h-5" />;
            default:
                return <Mic className="w-5 h-5" />;
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
            <div className="bg-[#1a1a1a] rounded-xl border border-white/10 w-full max-w-md mx-4 shadow-2xl">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-white/10">
                    <h2 className="text-lg font-semibold text-white">Select Audio Source</h2>
                    <button
                        onClick={onClose}
                        className="p-1 rounded-lg hover:bg-white/10 transition-colors"
                    >
                        <X className="w-5 h-5 text-gray-400" />
                    </button>
                </div>

                {/* Content */}
                <div className="p-4">
                    {isLoading ? (
                        <div className="flex items-center justify-center py-8">
                            <div className="w-6 h-6 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
                        </div>
                    ) : error ? (
                        <div className="text-center py-8">
                            <p className="text-red-400 mb-4">{error}</p>
                            <button
                                onClick={fetchDevices}
                                className="px-4 py-2 bg-white/10 rounded-lg hover:bg-white/20 transition-colors text-white"
                            >
                                Retry
                            </button>
                        </div>
                    ) : (
                        <div className="space-y-2">
                            {devices.map((device) => (
                                <button
                                    key={device.id}
                                    onClick={() => device.available && setSelectedDevice(device.id)}
                                    disabled={!device.available}
                                    className={`w-full flex items-center gap-3 p-3 rounded-lg transition-all ${selectedDevice === device.id
                                            ? 'bg-purple-600/30 border border-purple-500'
                                            : device.available
                                                ? 'bg-white/5 border border-transparent hover:bg-white/10'
                                                : 'bg-white/5 border border-transparent opacity-50 cursor-not-allowed'
                                        }`}
                                >
                                    <div className={`p-2 rounded-lg ${selectedDevice === device.id ? 'bg-purple-600' : 'bg-white/10'
                                        }`}>
                                        {getDeviceIcon(device.id)}
                                    </div>
                                    <div className="flex-1 text-left">
                                        <p className="text-white font-medium">{device.name}</p>
                                        {!device.available && (
                                            <p className="text-xs text-gray-500">Not available</p>
                                        )}
                                    </div>
                                    {selectedDevice === device.id && (
                                        <Check className="w-5 h-5 text-purple-400" />
                                    )}
                                </button>
                            ))}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="flex gap-3 p-4 border-t border-white/10">
                    <button
                        onClick={onClose}
                        className="flex-1 px-4 py-2.5 rounded-lg bg-white/10 hover:bg-white/20 transition-colors text-white font-medium"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleConfirm}
                        disabled={isLoading || !!error}
                        className="flex-1 px-4 py-2.5 rounded-lg bg-purple-600 hover:bg-purple-700 transition-colors text-white font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        Start Recording
                    </button>
                </div>
            </div>
        </div>
    );
}
