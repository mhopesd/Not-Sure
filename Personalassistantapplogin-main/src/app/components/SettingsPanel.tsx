import { useState, useEffect } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Loader2, Key, CheckCircle2, AlertCircle } from 'lucide-react';

interface SettingsPanelProps {
  projectId: string;
  publicAnonKey: string;
}

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

export function SettingsPanel({ projectId, publicAnonKey }: SettingsPanelProps) {
  const [provider, setProvider] = useState<LLMProvider>('openai');
  const [apiKey, setApiKey] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [isChecking, setIsChecking] = useState(true);
  const [isConfigured, setIsConfigured] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');

  const checkApiKeyStatus = async () => {
    setIsChecking(true);
    try {
      const response = await fetch(
        `https://${projectId}.supabase.co/functions/v1/make-server-7ea82c69/settings/api-key?provider=${provider}`,
        {
          headers: {
            'Authorization': `Bearer ${publicAnonKey}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setIsConfigured(data.configured);
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
        `https://${projectId}.supabase.co/functions/v1/make-server-7ea82c69/settings/api-key`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${publicAnonKey}`,
          },
          body: JSON.stringify({ provider, apiKey }),
        }
      );

      if (response.ok) {
        setIsConfigured(true);
        setSaveMessage('API key saved successfully!');
        setApiKey('');
        setTimeout(() => setSaveMessage(''), 3000);
      } else {
        const error = await response.json();
        setSaveMessage(`Error: ${error.error || 'Failed to save API key'}`);
      }
    } catch (error) {
      console.error('Error saving API key:', error);
      setSaveMessage('Network error: Could not save API key');
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
              <CheckCircle2 className="w-4 h-4 text-green-600" />
            ) : (
              <AlertCircle className="w-4 h-4 text-yellow-600" />
            )}
          </div>
          
          <p className="text-sm text-gray-600 mb-4">
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
                <p className="text-sm text-gray-600 mb-2 mt-1">
                  Get your API key from{' '}
                  <a
                    href={currentProvider.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline"
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
              <p className={`text-sm ${saveMessage.includes('Error') ? 'text-red-600' : 'text-green-600'}`}>
                {saveMessage}
              </p>
            )}
          </div>
        </div>

        <div className="pt-4 border-t">
          <h3 className="mb-2">Calendar Integration</h3>
          <p className="text-sm text-gray-600 mb-3">
            Calendar integration coming soon. This will allow automatic meeting creation from your calendar events.
          </p>
          <Button variant="outline" disabled>
            Connect Calendar
          </Button>
        </div>

        <div className="pt-4 border-t">
          <h3 className="mb-2">About</h3>
          <p className="text-sm text-gray-600">
            This personal assistant helps you record meetings, transcribe them, and use AI to extract action items and optimize your workflow.
          </p>
        </div>
      </div>
    </Card>
  );
}