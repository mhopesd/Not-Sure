import { useState, useEffect, useCallback } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import {
    Loader2,
    CheckCircle2,
    AlertCircle,
    Mail,
    Calendar,
    Settings2,
    ExternalLink,
    Unplug,
    ChevronDown,
    ChevronUp,
    Shield,
} from 'lucide-react';
import { getApiUrl, getApiHeaders } from '../config/api';

interface ProviderStatus {
    connected: boolean;
    has_credentials: boolean;
    email: string | null;
    display_name: string | null;
}

interface IntegrationStatus {
    microsoft: ProviderStatus;
    google: ProviderStatus;
}

const providerMeta = {
    microsoft: {
        label: 'Microsoft',
        description: 'Outlook email & Calendar',
        icon: '🪟',
        color: 'from-blue-500 to-blue-700',
        bgLight: 'bg-blue-50',
        textColor: 'text-blue-700',
        borderColor: 'border-blue-200',
        features: ['Outlook Email', 'Calendar Sync'],
        credentialsHelp: 'Register an app in Azure Portal → App Registrations → New Registration',
        credentialsLink: 'https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade',
        redirectUri: 'http://localhost:8000/api/integrations/microsoft/callback',
        scopes: 'Mail.Send, Calendars.ReadWrite',
    },
    google: {
        label: 'Google',
        description: 'Gmail & Google Calendar',
        icon: '🔵',
        color: 'from-red-500 to-yellow-500',
        bgLight: 'bg-red-50',
        textColor: 'text-red-700',
        borderColor: 'border-red-200',
        features: ['Gmail', 'Google Calendar'],
        credentialsHelp: 'Create OAuth 2.0 Client ID in Google Cloud Console → APIs & Services → Credentials',
        credentialsLink: 'https://console.cloud.google.com/apis/credentials',
        redirectUri: 'http://localhost:8000/api/integrations/google/callback',
        scopes: 'gmail.send, calendar.events',
    },
};

type Provider = keyof typeof providerMeta;

export function IntegrationsPanel() {
    const [status, setStatus] = useState<IntegrationStatus | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [expandedCredentials, setExpandedCredentials] = useState<Provider | null>(null);
    const [clientId, setClientId] = useState('');
    const [clientSecret, setClientSecret] = useState('');
    const [isSavingCreds, setIsSavingCreds] = useState(false);
    const [credMessage, setCredMessage] = useState('');
    const [connectingProvider, setConnectingProvider] = useState<Provider | null>(null);

    const fetchStatus = useCallback(async () => {
        try {
            const response = await fetch(getApiUrl('/api/integrations/status'), {
                headers: getApiHeaders(),
            });
            if (response.ok) {
                const data = await response.json();
                setStatus(data);
            }
        } catch (error) {
            console.error('Failed to fetch integration status:', error);
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchStatus();
    }, [fetchStatus]);

    // Listen for OAuth popup completion
    useEffect(() => {
        const handleMessage = (event: MessageEvent) => {
            if (event.data?.type === 'oauth_success') {
                setConnectingProvider(null);
                fetchStatus();
            } else if (event.data?.type === 'oauth_error') {
                setConnectingProvider(null);
                console.error('OAuth error:', event.data.error);
            }
        };
        window.addEventListener('message', handleMessage);
        return () => window.removeEventListener('message', handleMessage);
    }, [fetchStatus]);

    const handleSaveCredentials = async (provider: Provider) => {
        if (!clientId.trim() || !clientSecret.trim()) {
            setCredMessage('Both Client ID and Client Secret are required');
            return;
        }

        setIsSavingCreds(true);
        setCredMessage('');

        try {
            const response = await fetch(getApiUrl('/api/integrations/credentials'), {
                method: 'PUT',
                headers: getApiHeaders(),
                body: JSON.stringify({
                    provider,
                    client_id: clientId,
                    client_secret: clientSecret,
                }),
            });

            if (response.ok) {
                setCredMessage('Credentials saved!');
                setClientId('');
                setClientSecret('');
                setExpandedCredentials(null);
                fetchStatus();
                setTimeout(() => setCredMessage(''), 3000);
            } else {
                const error = await response.json();
                setCredMessage(`Error: ${error.detail || 'Failed to save'}`);
            }
        } catch (error) {
            setCredMessage('Network error saving credentials');
        } finally {
            setIsSavingCreds(false);
        }
    };

    const handleConnect = async (provider: Provider) => {
        setConnectingProvider(provider);
        try {
            const response = await fetch(getApiUrl(`/api/integrations/${provider}/auth`), {
                headers: getApiHeaders(),
            });

            if (response.ok) {
                const { auth_url } = await response.json();
                // Open OAuth popup
                const popup = window.open(
                    auth_url,
                    `${provider}_oauth`,
                    'width=600,height=700,scrollbars=yes'
                );

                // Monitor popup close
                const checkClosed = setInterval(() => {
                    if (popup?.closed) {
                        clearInterval(checkClosed);
                        setConnectingProvider(null);
                        fetchStatus();
                    }
                }, 1000);
            } else {
                const error = await response.json();
                if (error.detail?.includes('credentials not configured')) {
                    setExpandedCredentials(provider);
                }
                setConnectingProvider(null);
            }
        } catch (error) {
            console.error('Error initiating OAuth:', error);
            setConnectingProvider(null);
        }
    };

    const handleDisconnect = async (provider: Provider) => {
        try {
            const response = await fetch(
                getApiUrl(`/api/integrations/${provider}/disconnect`),
                {
                    method: 'DELETE',
                    headers: getApiHeaders(),
                }
            );
            if (response.ok) {
                fetchStatus();
            }
        } catch (error) {
            console.error('Error disconnecting:', error);
        }
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {(Object.keys(providerMeta) as Provider[]).map((provider) => {
                const meta = providerMeta[provider];
                const providerStatus = status?.[provider];
                const isConnected = providerStatus?.connected || false;
                const hasCreds = providerStatus?.has_credentials || false;
                const isConnecting = connectingProvider === provider;
                const isExpanded = expandedCredentials === provider;

                return (
                    <Card key={provider} className={`overflow-hidden transition-all duration-200 ${isConnected ? `border-2 ${meta.borderColor}` : ''}`}>
                        {/* Header */}
                        <div className="p-5">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${meta.color} flex items-center justify-center text-white text-lg shadow-sm`}>
                                        {meta.icon}
                                    </div>
                                    <div>
                                        <h4 className="font-semibold text-gray-900">{meta.label}</h4>
                                        <p className="text-sm text-gray-500">{meta.description}</p>
                                    </div>
                                </div>

                                <div className="flex items-center gap-2">
                                    {isConnected ? (
                                        <>
                                            <div className="flex items-center gap-1.5 px-3 py-1 bg-green-50 rounded-full">
                                                <CheckCircle2 className="w-3.5 h-3.5 text-green-600" />
                                                <span className="text-xs font-medium text-green-700">Connected</span>
                                            </div>
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                onClick={() => handleDisconnect(provider)}
                                                className="text-gray-400 hover:text-red-500"
                                            >
                                                <Unplug className="w-4 h-4" />
                                            </Button>
                                        </>
                                    ) : (
                                        <Button
                                            onClick={() => hasCreds ? handleConnect(provider) : setExpandedCredentials(isExpanded ? null : provider)}
                                            disabled={isConnecting}
                                            size="sm"
                                        >
                                            {isConnecting ? (
                                                <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                                            ) : !hasCreds ? (
                                                <Settings2 className="w-4 h-4 mr-1" />
                                            ) : (
                                                <ExternalLink className="w-4 h-4 mr-1" />
                                            )}
                                            {isConnecting ? 'Connecting...' : !hasCreds ? 'Configure' : 'Connect'}
                                        </Button>
                                    )}
                                </div>
                            </div>

                            {/* Connected account info */}
                            {isConnected && providerStatus?.email && (
                                <div className={`mt-3 p-3 ${meta.bgLight} rounded-lg`}>
                                    <div className="flex items-center gap-4 text-sm">
                                        <div className="flex items-center gap-1.5">
                                            <Mail className="w-3.5 h-3.5 text-gray-500" />
                                            <span className="text-gray-700">{providerStatus.email}</span>
                                        </div>
                                        {providerStatus.display_name && (
                                            <span className="text-gray-500">({providerStatus.display_name})</span>
                                        )}
                                    </div>
                                    <div className="flex gap-2 mt-2">
                                        {meta.features.map((feature) => (
                                            <span
                                                key={feature}
                                                className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${meta.bgLight} ${meta.textColor}`}
                                            >
                                                {feature.includes('Calendar') ? (
                                                    <Calendar className="w-3 h-3" />
                                                ) : (
                                                    <Mail className="w-3 h-3" />
                                                )}
                                                {feature}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Credential setup toggle for connected accounts */}
                            {isConnected && (
                                <button
                                    onClick={() => setExpandedCredentials(isExpanded ? null : provider)}
                                    className="mt-2 text-xs text-gray-400 hover:text-gray-600 flex items-center gap-1"
                                >
                                    <Settings2 className="w-3 h-3" />
                                    Manage credentials
                                    {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                                </button>
                            )}
                        </div>

                        {/* Expandable credentials section */}
                        {isExpanded && (
                            <div className="border-t bg-gray-50 p-5 space-y-4">
                                <div className="flex items-start gap-2">
                                    <Shield className="w-4 h-4 text-gray-400 mt-0.5 shrink-0" />
                                    <div>
                                        <p className="text-sm text-gray-600">{meta.credentialsHelp}</p>
                                        <a
                                            href={meta.credentialsLink}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="inline-flex items-center gap-1 text-sm text-blue-600 hover:underline mt-1"
                                        >
                                            Open Developer Console <ExternalLink className="w-3 h-3" />
                                        </a>
                                    </div>
                                </div>

                                <div className="bg-white p-3 rounded-lg border text-xs text-gray-500 space-y-1">
                                    <p><strong>Redirect URI:</strong> <code className="bg-gray-100 px-1 rounded">{meta.redirectUri}</code></p>
                                    <p><strong>Scopes:</strong> <code className="bg-gray-100 px-1 rounded">{meta.scopes}</code></p>
                                </div>

                                <div className="space-y-3">
                                    <div>
                                        <Label htmlFor={`${provider}-client-id`}>Client ID</Label>
                                        <Input
                                            id={`${provider}-client-id`}
                                            value={clientId}
                                            onChange={(e) => setClientId(e.target.value)}
                                            placeholder="Enter Client ID"
                                            className="mt-1"
                                        />
                                    </div>
                                    <div>
                                        <Label htmlFor={`${provider}-client-secret`}>Client Secret</Label>
                                        <Input
                                            id={`${provider}-client-secret`}
                                            type="password"
                                            value={clientSecret}
                                            onChange={(e) => setClientSecret(e.target.value)}
                                            placeholder="Enter Client Secret"
                                            className="mt-1"
                                        />
                                    </div>

                                    <div className="flex items-center gap-3">
                                        <Button
                                            onClick={() => handleSaveCredentials(provider)}
                                            disabled={isSavingCreds || !clientId.trim() || !clientSecret.trim()}
                                            size="sm"
                                        >
                                            {isSavingCreds && <Loader2 className="w-4 h-4 mr-1 animate-spin" />}
                                            Save Credentials
                                        </Button>
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            onClick={() => {
                                                setExpandedCredentials(null);
                                                setClientId('');
                                                setClientSecret('');
                                                setCredMessage('');
                                            }}
                                        >
                                            Cancel
                                        </Button>
                                    </div>

                                    {credMessage && (
                                        <p className={`text-sm ${credMessage.includes('Error') || credMessage.includes('required') ? 'text-red-600' : 'text-green-600'}`}>
                                            {credMessage}
                                        </p>
                                    )}
                                </div>
                            </div>
                        )}
                    </Card>
                );
            })}

            {/* Info note */}
            <div className="flex items-start gap-2 p-3 bg-amber-50 rounded-lg text-sm text-amber-800">
                <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                <div>
                    <p className="font-medium">Getting Started</p>
                    <p className="text-amber-700 mt-0.5">
                        To connect a service, you'll first need to register your app in the provider's developer console
                        and enter the Client ID and Secret above. Your credentials are stored locally and never shared.
                    </p>
                </div>
            </div>
        </div>
    );
}
