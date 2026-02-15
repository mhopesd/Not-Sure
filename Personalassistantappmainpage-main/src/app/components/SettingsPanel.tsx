import { useState, useEffect } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Loader2, Key, CheckCircle2, AlertCircle } from 'lucide-react';
import { getApiUrl, getApiHeaders } from '../config/api';
import { IntegrationsPanel } from './IntegrationsPanel';

// No props needed - uses local API configuration
type LLMProvider = 'openai' | 'google' | 'claude' | 'other';

const providerInfo = {
  openai: {
    label: 'OpenAI',
    placeholder: 'sk-...',
    link: 'https://platform.openai.com/api-keys',
    description: 'GPT-4 and other OpenAI models'
  },
  google: {
    label: 'Google (Gemini)',
    placeholder: 'AIza...',
    link: 'https://aistudio.google.com/app/apikey',
    description: 'Google Gemini models'
  },
  claude: {
    label: 'Anthropic (Claude)',
    placeholder: 'sk-ant-...',
    link: 'https://console.anthropic.com/settings/keys',
    description: 'Claude 3 and other Anthropic models'
  },
  other: {
    label: 'Other',
    placeholder: 'Enter your API key',
    link: '',
    description: 'Custom LLM provider'
  }
};

export function SettingsPanel() {
  const [provider, setProvider] = useState<LLMProvider>('google'); // Default to Google for Gemini
  const [apiKey, setApiKey] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [isChecking, setIsChecking] = useState(true);
  const [isConfigured, setIsConfigured] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');

  const checkApiKeyStatus = async () => {
    setIsChecking(true);
    try {
      const response = await fetch(
        getApiUrl('/api/settings'),
        {
          headers: getApiHeaders(),
        }
      );

      if (response.ok) {
        const data = await response.json();
        setIsConfigured(data.has_gemini_key || false);
        // Set provider based on current config
        if (data.llm_provider) {
          setProvider(data.llm_provider === 'gemini' ? 'google' : data.llm_provider as LLMProvider);
        }
      }
    } catch (error) {
      console.error('Error checking API key status:', error);
    } finally {
      setIsChecking(false);
    }
  };

  useEffect(() => {
    checkApiKeyStatus();
  }, [provider]);

  const handleSaveApiKey = async () => {
    if (!apiKey.trim()) {
      setSaveMessage('Please enter an API key');
      return;
    }

    setIsSaving(true);
    setSaveMessage('');

    try {
      const response = await fetch(
        getApiUrl('/api/settings'),
        {
          method: 'PUT',
          headers: getApiHeaders(),
          body: JSON.stringify({
            gemini_api_key: provider === 'google' ? apiKey : undefined,
            llm_provider: provider === 'google' ? 'gemini' : provider
          }),
        }
      );

      if (response.ok) {
        setIsConfigured(true);
        setSaveMessage('API key saved successfully!');
        setApiKey('');
        setTimeout(() => setSaveMessage(''), 3000);
      } else {
        const error = await response.json();
        setSaveMessage(`Error: ${error.detail || 'Failed to save API key'}`);
      }
    } catch (error) {
      console.error('Error saving API key:', error);
      setSaveMessage('Network error: Could not save API key. Is the API server running?');
    } finally {
      setIsSaving(false);
    }
  };

  const currentProvider = providerInfo[provider];

  return (
    <Card className="p-6">
      <h2 className="mb-4">Settings</h2>

      <div className="space-y-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Key className="w-4 h-4" />
            <Label>LLM Provider Configuration</Label>
            {isChecking ? (
              <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
            ) : isConfigured ? (
              <CheckCircle2 className="w-4 h-4 text-green-400" />
            ) : (
              <AlertCircle className="w-4 h-4 text-yellow-400" />
            )}
          </div>

          <p className="text-sm text-gray-400 mb-4">
            Required for AI analysis of meetings and journal entries. Select your preferred LLM provider.
          </p>

          <div className="space-y-4">
            <div>
              <Label htmlFor="provider">Provider</Label>
              <Select value={provider} onValueChange={(value) => setProvider(value as LLMProvider)}>
                <SelectTrigger id="provider">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="openai">OpenAI (GPT-4, GPT-4o-mini)</SelectItem>
                  <SelectItem value="google">Google (Gemini)</SelectItem>
                  <SelectItem value="claude">Anthropic (Claude)</SelectItem>
                  <SelectItem value="other">Other</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-sm text-gray-500 mt-1">{currentProvider.description}</p>
            </div>

            <div>
              <Label htmlFor="api-key">{currentProvider.label} API Key</Label>
              {currentProvider.link && (
                <p className="text-sm text-gray-400 mb-2 mt-1">
                  Get your API key from{' '}
                  <a
                    href={currentProvider.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-400 hover:underline"
                  >
                    {currentProvider.label}
                  </a>
                </p>
              )}
              <Input
                id="api-key"
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder={currentProvider.placeholder}
              />
            </div>

            <Button
              onClick={handleSaveApiKey}
              disabled={isSaving || !apiKey.trim()}
            >
              {isSaving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Save API Key
            </Button>

            {saveMessage && (
              <p className={`text-sm ${saveMessage.includes('Error') ? 'text-red-400' : 'text-green-400'}`}>
                {saveMessage}
              </p>
            )}
          </div>
        </div>

        <div className="pt-4 border-t">
          <h3 className="mb-2">Service Integrations</h3>
          <p className="text-sm text-gray-400 mb-4">
            Connect your Outlook, Gmail, and Calendar accounts to sync events and share meeting summaries.
          </p>
          <IntegrationsPanel />
        </div>

        <div className="pt-4 border-t">
          <h3 className="mb-2">About</h3>
          <p className="text-sm text-gray-400">
            This personal assistant helps you record meetings, transcribe them, and use AI to extract action items and optimize your workflow.
          </p>
        </div>
      </div>
    </Card>
  );
}