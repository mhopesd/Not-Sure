import { Card } from './ui/card';
import { Button } from './ui/button';
import { X } from 'lucide-react';

interface TermsOfServiceProps {
  onClose: () => void;
}

export function TermsOfService({ onClose }: TermsOfServiceProps) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-6 z-50 overflow-y-auto">
      <Card className="w-full max-w-3xl max-h-[90vh] overflow-y-auto p-8 relative">
        <Button
          onClick={onClose}
          variant="ghost"
          size="sm"
          className="absolute top-4 right-4"
        >
          <X className="w-5 h-5" />
        </Button>

        <div className="space-y-6">
          <div>
            <h1 className="mb-2">Terms of Service</h1>
            <p className="text-sm text-gray-500">Last updated: January 3, 2026</p>
          </div>

          <div className="space-y-6 text-sm">
            <section>
              <h2 className="mb-3">1. Acceptance of Terms</h2>
              <p className="text-gray-700 leading-relaxed">
                By accessing and using Personal Assistant ("the Service"), you accept and agree to be bound by the terms and provision of this agreement. If you do not agree to these Terms of Service, please do not use the Service.
              </p>
            </section>

            <section>
              <h2 className="mb-3">2. Description of Service</h2>
              <p className="text-gray-700 leading-relaxed mb-3">
                Personal Assistant provides users with tools to:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-gray-700">
                <li>Record and transcribe meetings and calls</li>
                <li>Store and analyze meeting transcripts using AI</li>
                <li>Maintain a personal journal with AI-powered insights</li>
                <li>Connect to calendar services for meeting management</li>
                <li>Extract action items and next steps from meetings</li>
              </ul>
            </section>

            <section>
              <h2 className="mb-3">3. User Responsibilities</h2>
              <p className="text-gray-700 leading-relaxed mb-3">
                You agree to:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-gray-700">
                <li>Provide accurate and complete information during registration</li>
                <li>Maintain the security of your account credentials</li>
                <li>Obtain necessary consents before recording any calls or meetings</li>
                <li>Comply with all applicable laws regarding call recording in your jurisdiction</li>
                <li>Not use the Service for any illegal or unauthorized purpose</li>
                <li>Not transmit any malicious code or viruses</li>
              </ul>
            </section>

            <section>
              <h2 className="mb-3">4. Recording Consent</h2>
              <p className="text-gray-700 leading-relaxed">
                You are solely responsible for obtaining all necessary consents and complying with all applicable laws before recording any calls, meetings, or conversations. The Service does not automatically notify participants that they are being recorded. You acknowledge that recording laws vary by jurisdiction and it is your responsibility to ensure compliance.
              </p>
            </section>

            <section>
              <h2 className="mb-3">5. Data Storage and API Keys</h2>
              <p className="text-gray-700 leading-relaxed">
                The Service stores your meeting transcripts, journal entries, and encrypted API keys securely. While we implement industry-standard security measures, you acknowledge that no method of transmission over the internet is 100% secure. You are responsible for the confidentiality of your API keys and any activity that occurs through your account.
              </p>
            </section>

            <section>
              <h2 className="mb-3">6. AI Analysis and LLM Providers</h2>
              <p className="text-gray-700 leading-relaxed">
                The Service uses third-party AI language models to analyze your content. When you use AI features, your data may be transmitted to your chosen LLM provider (OpenAI, Google, Anthropic, or others). You are responsible for reviewing and complying with your chosen provider's terms of service and data usage policies.
              </p>
            </section>

            <section>
              <h2 className="mb-3">7. Intellectual Property</h2>
              <p className="text-gray-700 leading-relaxed">
                You retain all rights to your content (recordings, transcripts, journal entries). By using the Service, you grant us a limited license to process, store, and analyze your content solely for the purpose of providing the Service to you.
              </p>
            </section>

            <section>
              <h2 className="mb-3">8. Service Availability</h2>
              <p className="text-gray-700 leading-relaxed">
                We strive to maintain high availability but do not guarantee uninterrupted service. The Service may be temporarily unavailable for maintenance, upgrades, or due to factors beyond our control. We are not liable for any loss of data or inability to access the Service.
              </p>
            </section>

            <section>
              <h2 className="mb-3">9. Limitation of Liability</h2>
              <p className="text-gray-700 leading-relaxed">
                To the maximum extent permitted by law, Personal Assistant shall not be liable for any indirect, incidental, special, consequential, or punitive damages, or any loss of profits or revenues, whether incurred directly or indirectly, or any loss of data, use, goodwill, or other intangible losses.
              </p>
            </section>

            <section>
              <h2 className="mb-3">10. Termination</h2>
              <p className="text-gray-700 leading-relaxed">
                We reserve the right to terminate or suspend your account at any time for violations of these Terms. Upon termination, your right to use the Service will immediately cease. You may terminate your account at any time by contacting us.
              </p>
            </section>

            <section>
              <h2 className="mb-3">11. Changes to Terms</h2>
              <p className="text-gray-700 leading-relaxed">
                We reserve the right to modify these Terms at any time. We will notify users of any material changes. Your continued use of the Service after changes constitute acceptance of the modified Terms.
              </p>
            </section>

            <section>
              <h2 className="mb-3">12. Contact Information</h2>
              <p className="text-gray-700 leading-relaxed">
                For questions about these Terms of Service, please contact us at legal@personalassistant.com
              </p>
            </section>
          </div>

          <div className="pt-4 border-t">
            <Button onClick={onClose} className="w-full">
              Close
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
