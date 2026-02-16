import { useState, useEffect } from 'react';
import { Mic, Key, Sparkles, ArrowRight, ArrowLeft, Check, Volume2, Radio, Loader2, ChevronRight, History, BookOpen } from 'lucide-react';
import { getApiUrl, getApiHeaders } from '../config/api';

interface OnboardingWizardProps {
    onComplete: () => void;
}

type LLMProvider = 'openai' | 'google' | 'claude';

const providerInfo: Record<LLMProvider, { label: string; placeholder: string; link: string; description: string }> = {
    google: {
        label: 'Google (Gemini)',
        placeholder: 'AIza...',
        link: 'https://aistudio.google.com/app/apikey',
        description: 'Recommended — powers transcription analysis & live insights'
    },
    openai: {
        label: 'OpenAI',
        placeholder: 'sk-...',
        link: 'https://platform.openai.com/api-keys',
        description: 'GPT-4 and other OpenAI models'
    },
    claude: {
        label: 'Anthropic (Claude)',
        placeholder: 'sk-ant-...',
        link: 'https://console.anthropic.com/settings/keys',
        description: 'Claude 3 and other Anthropic models'
    }
};

interface Device {
    id: string;
    name: string;
    available: boolean;
}

export function OnboardingWizard({ onComplete }: OnboardingWizardProps) {
    const [step, setStep] = useState(0);
    const [direction, setDirection] = useState<'forward' | 'back'>('forward');

    // Step 2: API Key
    const [provider, setProvider] = useState<LLMProvider>('google');
    const [apiKey, setApiKey] = useState('');
    const [isSavingKey, setIsSavingKey] = useState(false);
    const [keySaved, setKeySaved] = useState(false);
    const [keyError, setKeyError] = useState('');

    // Step 3: Microphone
    const [devices, setDevices] = useState<Device[]>([]);
    const [selectedDevice, setSelectedDevice] = useState('microphone');
    const [isLoadingDevices, setIsLoadingDevices] = useState(false);
    const [deviceError, setDeviceError] = useState('');

    const totalSteps = 4;

    const goNext = () => {
        setDirection('forward');
        setStep(s => Math.min(s + 1, totalSteps - 1));
    };

    const goBack = () => {
        setDirection('back');
        setStep(s => Math.max(s - 1, 0));
    };

    // Load devices when reaching step 3
    useEffect(() => {
        if (step === 2) {
            fetchDevices();
        }
    }, [step]);

    const fetchDevices = async () => {
        setIsLoadingDevices(true);
        setDeviceError('');
        try {
            const response = await fetch(getApiUrl('/api/devices'), {
                headers: getApiHeaders()
            });
            if (!response.ok) throw new Error('Failed to fetch devices');
            const data = await response.json();
            setDevices(data.devices || []);
            setSelectedDevice(data.default || 'microphone');
        } catch {
            setDeviceError('Could not load audio devices. Make sure the backend is running.');
        } finally {
            setIsLoadingDevices(false);
        }
    };

    const handleSaveApiKey = async () => {
        if (!apiKey.trim()) return;
        setIsSavingKey(true);
        setKeyError('');

        try {
            const response = await fetch(getApiUrl('/api/settings'), {
                method: 'PUT',
                headers: getApiHeaders(),
                body: JSON.stringify({
                    gemini_api_key: provider === 'google' ? apiKey : undefined,
                    llm_provider: provider === 'google' ? 'gemini' : provider
                })
            });

            if (response.ok) {
                setKeySaved(true);
                setTimeout(goNext, 600);
            } else {
                const err = await response.json();
                setKeyError(err.detail || 'Failed to save key');
            }
        } catch {
            setKeyError('Network error — is the backend running?');
        } finally {
            setIsSavingKey(false);
        }
    };

    const getDeviceIcon = (id: string) => {
        if (id === 'system') return <Volume2 className="w-5 h-5" />;
        if (id === 'hybrid') return <Radio className="w-5 h-5" />;
        return <Mic className="w-5 h-5" />;
    };

    return (
        <div className="min-h-screen bg-[#111] flex items-center justify-center p-6">
            <div className="w-full max-w-lg">
                {/* Progress dots */}
                <div className="flex justify-center gap-2 mb-8">
                    {Array.from({ length: totalSteps }).map((_, i) => (
                        <div
                            key={i}
                            className={`h-1.5 rounded-full transition-all duration-300 ${i === step
                                ? 'w-8 bg-[#2774AE]'
                                : i < step
                                    ? 'w-4 bg-[#2774AE]/50'
                                    : 'w-4 bg-white/10'
                                }`}
                        />
                    ))}
                </div>

                {/* Card */}
                <div className="bg-[#1a1a1a] border border-white/10 rounded-2xl p-8 shadow-2xl backdrop-blur-sm">
                    {/* Step 0: Welcome */}
                    {step === 0 && (
                        <div className="text-center space-y-6 animate-fadeIn">
                            <div className="w-20 h-20 mx-auto rounded-2xl bg-gradient-to-br from-[#2774AE] to-[#1e5f8e] flex items-center justify-center shadow-lg shadow-[#2774AE]/20">
                                <Mic className="w-10 h-10 text-white" />
                            </div>

                            <div>
                                <h1 className="text-3xl font-bold text-white mb-2">
                                    Personal Assistant
                                </h1>
                                <p className="text-gray-400 text-lg">
                                    Record meetings, get AI summaries, and never lose a key insight again.
                                </p>
                            </div>

                            <div className="grid grid-cols-3 gap-3 pt-2">
                                {[
                                    { icon: <Mic className="w-5 h-5" />, label: 'Record' },
                                    { icon: <Sparkles className="w-5 h-5" />, label: 'Analyze' },
                                    { icon: <History className="w-5 h-5" />, label: 'Review' }
                                ].map((item) => (
                                    <div key={item.label} className="p-3 rounded-xl bg-white/5 text-center">
                                        <div className="text-[#FFD100] flex justify-center mb-1">{item.icon}</div>
                                        <span className="text-xs text-gray-400">{item.label}</span>
                                    </div>
                                ))}
                            </div>

                            <button
                                onClick={goNext}
                                className="w-full flex items-center justify-center gap-2 px-6 py-3.5 bg-[#2774AE] hover:bg-[#1e5f8e] rounded-xl text-white font-semibold text-lg transition-all transform hover:scale-[1.02] shadow-lg shadow-[#2774AE]/25"
                            >
                                Get Started
                                <ArrowRight className="w-5 h-5" />
                            </button>
                        </div>
                    )}

                    {/* Step 1: API Key */}
                    {step === 1 && (
                        <div className="space-y-6 animate-fadeIn">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-xl bg-[#FFD100]/10 flex items-center justify-center">
                                    <Key className="w-5 h-5 text-[#FFD100]" />
                                </div>
                                <div>
                                    <h2 className="text-xl font-bold text-white">Connect AI</h2>
                                    <p className="text-sm text-gray-400">Powers smart summaries & speaker detection</p>
                                </div>
                            </div>

                            {/* Provider picker */}
                            <div className="space-y-2">
                                <label className="text-sm text-gray-400">Provider</label>
                                <div className="grid grid-cols-3 gap-2">
                                    {(Object.keys(providerInfo) as LLMProvider[]).map((key) => (
                                        <button
                                            key={key}
                                            onClick={() => { setProvider(key); setKeySaved(false); setKeyError(''); }}
                                            className={`p-2.5 rounded-lg text-sm font-medium transition-all ${provider === key
                                                ? 'bg-[#2774AE]/20 border border-[#2774AE] text-white'
                                                : 'bg-white/5 border border-white/10 text-gray-400 hover:bg-white/10'
                                                }`}
                                        >
                                            {providerInfo[key].label.split(' ')[0]}
                                        </button>
                                    ))}
                                </div>
                                <p className="text-xs text-gray-500">{providerInfo[provider].description}</p>
                            </div>

                            {/* Key input */}
                            <div className="space-y-2">
                                <label className="text-sm text-gray-400">
                                    API Key —{' '}
                                    <a
                                        href={providerInfo[provider].link}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-[#2774AE] hover:underline"
                                    >
                                        Get one free →
                                    </a>
                                </label>
                                <input
                                    type="password"
                                    value={apiKey}
                                    onChange={(e) => { setApiKey(e.target.value); setKeyError(''); }}
                                    placeholder={providerInfo[provider].placeholder}
                                    className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-[#2774AE] transition-colors"
                                />
                            </div>

                            {keyError && (
                                <p className="text-sm text-red-400">{keyError}</p>
                            )}

                            <div className="flex gap-3">
                                <button
                                    onClick={goBack}
                                    className="p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors"
                                >
                                    <ArrowLeft className="w-5 h-5 text-gray-400" />
                                </button>

                                <button
                                    onClick={handleSaveApiKey}
                                    disabled={isSavingKey || !apiKey.trim()}
                                    className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-[#2774AE] hover:bg-[#1e5f8e] disabled:opacity-50 disabled:cursor-not-allowed rounded-xl text-white font-semibold transition-all"
                                >
                                    {isSavingKey ? (
                                        <Loader2 className="w-5 h-5 animate-spin" />
                                    ) : keySaved ? (
                                        <><Check className="w-5 h-5" /> Saved!</>
                                    ) : (
                                        <>Save & Continue</>
                                    )}
                                </button>
                            </div>

                            <button
                                onClick={goNext}
                                className="w-full text-center text-sm text-gray-500 hover:text-gray-300 transition-colors"
                            >
                                Skip for now — you can add it later in Settings
                            </button>
                        </div>
                    )}

                    {/* Step 2: Microphone */}
                    {step === 2 && (
                        <div className="space-y-6 animate-fadeIn">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-xl bg-[#2774AE]/10 flex items-center justify-center">
                                    <Mic className="w-5 h-5 text-[#2774AE]" />
                                </div>
                                <div>
                                    <h2 className="text-xl font-bold text-white">Audio Source</h2>
                                    <p className="text-sm text-gray-400">Choose how you'll capture audio</p>
                                </div>
                            </div>

                            {isLoadingDevices ? (
                                <div className="flex items-center justify-center py-8">
                                    <Loader2 className="w-6 h-6 text-[#2774AE] animate-spin" />
                                </div>
                            ) : deviceError ? (
                                <div className="text-center py-6">
                                    <p className="text-red-400 text-sm mb-3">{deviceError}</p>
                                    <button
                                        onClick={fetchDevices}
                                        className="px-4 py-2 bg-white/10 rounded-lg hover:bg-white/20 transition-colors text-white text-sm"
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
                                            className={`w-full flex items-center gap-3 p-3.5 rounded-xl transition-all ${selectedDevice === device.id
                                                ? 'bg-[#2774AE]/20 border border-[#2774AE]'
                                                : device.available
                                                    ? 'bg-white/5 border border-white/10 hover:bg-white/10'
                                                    : 'bg-white/5 border border-white/10 opacity-40 cursor-not-allowed'
                                                }`}
                                        >
                                            <div className={`p-2 rounded-lg ${selectedDevice === device.id ? 'bg-[#2774AE]' : 'bg-white/10'
                                                }`}>
                                                {getDeviceIcon(device.id)}
                                            </div>
                                            <span className="text-white font-medium flex-1 text-left">{device.name}</span>
                                            {selectedDevice === device.id && (
                                                <Check className="w-5 h-5 text-[#FFD100]" />
                                            )}
                                        </button>
                                    ))}
                                </div>
                            )}

                            <div className="flex gap-3">
                                <button
                                    onClick={goBack}
                                    className="p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors"
                                >
                                    <ArrowLeft className="w-5 h-5 text-gray-400" />
                                </button>
                                <button
                                    onClick={goNext}
                                    className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-[#2774AE] hover:bg-[#1e5f8e] rounded-xl text-white font-semibold transition-all"
                                >
                                    Continue
                                    <ArrowRight className="w-5 h-5" />
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Step 3: Ready */}
                    {step === 3 && (
                        <div className="text-center space-y-6 animate-fadeIn">
                            <div className="w-16 h-16 mx-auto rounded-full bg-[#FFD100]/10 flex items-center justify-center">
                                <Check className="w-8 h-8 text-[#FFD100]" />
                            </div>

                            <div>
                                <h2 className="text-2xl font-bold text-white mb-2">You're All Set!</h2>
                                <p className="text-gray-400">Here's what you can do:</p>
                            </div>

                            <div className="space-y-3 text-left">
                                {[
                                    {
                                        icon: <Mic className="w-5 h-5 text-[#2774AE]" />,
                                        title: 'Record a meeting',
                                        desc: "Hit record and we'll transcribe + summarize with speaker labels"
                                    },
                                    {
                                        icon: <History className="w-5 h-5 text-[#2774AE]" />,
                                        title: 'Browse past meetings',
                                        desc: 'Search transcripts, view diarized speakers, export action items'
                                    },
                                    {
                                        icon: <BookOpen className="w-5 h-5 text-[#2774AE]" />,
                                        title: 'Keep a journal',
                                        desc: 'Daily reflection with AI-powered writing suggestions'
                                    }
                                ].map((item) => (
                                    <div key={item.title} className="flex items-start gap-3 p-3 rounded-xl bg-white/5">
                                        <div className="p-2 rounded-lg bg-[#2774AE]/10 flex-shrink-0">
                                            {item.icon}
                                        </div>
                                        <div>
                                            <p className="text-white font-medium text-sm">{item.title}</p>
                                            <p className="text-gray-500 text-xs">{item.desc}</p>
                                        </div>
                                        <ChevronRight className="w-4 h-4 text-gray-600 mt-1 flex-shrink-0" />
                                    </div>
                                ))}
                            </div>

                            <div className="flex gap-3">
                                <button
                                    onClick={goBack}
                                    className="p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors"
                                >
                                    <ArrowLeft className="w-5 h-5 text-gray-400" />
                                </button>
                                <button
                                    onClick={onComplete}
                                    className="flex-1 flex items-center justify-center gap-2 px-6 py-3.5 bg-[#2774AE] hover:bg-[#1e5f8e] rounded-xl text-white font-semibold text-lg transition-all transform hover:scale-[1.02] shadow-lg shadow-[#2774AE]/25"
                                >
                                    Start Using App
                                    <ArrowRight className="w-5 h-5" />
                                </button>
                            </div>
                        </div>
                    )}
                </div>

                {/* Step label */}
                <p className="text-center text-xs text-gray-600 mt-4">
                    Step {step + 1} of {totalSteps}
                </p>
            </div>
        </div>
    );
}
