import { Card } from './ui/card';
import { Button } from './ui/button';
import { X } from 'lucide-react';

interface PrivacyPolicyProps {
  onClose: () => void;
}

export function PrivacyPolicy({ onClose }: PrivacyPolicyProps) {
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
            <h1 className="mb-2">Privacy Policy</h1>
            <p className="text-sm text-gray-500">Last updated: January 3, 2026</p>
          </div>

          <div className="space-y-6 text-sm">
            <section>
              <h2 className="mb-3">1. Introduction</h2>
              <p className="text-gray-700 leading-relaxed">
                Personal Assistant ("we", "our", or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our Service. Please read this privacy policy carefully.
              </p>
            </section>

            <section>
              <h2 className="mb-3">2. Information We Collect</h2>
              <p className="text-gray-700 leading-relaxed mb-3">
                We collect information that you provide directly to us:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-gray-700">
                <li><strong>Account Information:</strong> Email address, name, password, and authentication credentials</li>
                <li><strong>Meeting Data:</strong> Call recordings, transcripts, speaker information, timestamps, and meeting metadata</li>
                <li><strong>Journal Entries:</strong> Personal journal text and associated timestamps</li>
                <li><strong>Calendar Data:</strong> Meeting schedules and calendar events when you connect your calendar</li>
                <li><strong>API Keys:</strong> Third-party LLM provider API keys (stored encrypted)</li>
                <li><strong>Usage Data:</strong> Information about how you interact with the Service</li>
              </ul>
            </section>

            <section>
              <h2 className="mb-3">3. How We Use Your Information</h2>
              <p className="text-gray-700 leading-relaxed mb-3">
                We use the collected information to:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-gray-700">
                <li>Provide, maintain, and improve the Service</li>
                <li>Process and store your meeting recordings and transcripts</li>
                <li>Analyze your content using AI when you request it</li>
                <li>Generate insights and next steps from your meetings and journal entries</li>
                <li>Authenticate your account and prevent unauthorized access</li>
                <li>Send you technical notices and support messages</li>
                <li>Respond to your comments and questions</li>
                <li>Comply with legal obligations</li>
              </ul>
            </section>

            <section>
              <h2 className="mb-3">4. Data Storage and Security</h2>
              <p className="text-gray-700 leading-relaxed">
                Your data is stored securely using Supabase infrastructure with industry-standard encryption. API keys are encrypted before storage. We implement appropriate technical and organizational measures to protect your personal information against unauthorized access, alteration, disclosure, or destruction. However, no internet or email transmission is ever fully secure or error-free.
              </p>
            </section>

            <section>
              <h2 className="mb-3">5. Third-Party Services</h2>
              <p className="text-gray-700 leading-relaxed mb-3">
                The Service integrates with third-party providers:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-gray-700">
                <li><strong>Authentication Providers:</strong> Google, Microsoft for sign-in services</li>
                <li><strong>LLM Providers:</strong> OpenAI, Google Gemini, Anthropic Claude, or custom providers for AI analysis</li>
                <li><strong>Calendar Services:</strong> Google Calendar, Microsoft Outlook, or other calendar providers</li>
                <li><strong>Infrastructure:</strong> Supabase for data storage and backend services</li>
              </ul>
              <p className="text-gray-700 leading-relaxed mt-3">
                When you use these integrations, your data may be transmitted to these third parties. Each provider has its own privacy policy governing the use of your data.
              </p>
            </section>

            <section>
              <h2 className="mb-3">6. Data Sharing and Disclosure</h2>
              <p className="text-gray-700 leading-relaxed mb-3">
                We do not sell your personal information. We may share your information only in the following circumstances:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-gray-700">
                <li>With third-party services you choose to integrate (LLM providers, calendar services)</li>
                <li>To comply with legal obligations or respond to lawful requests</li>
                <li>To protect our rights, privacy, safety, or property</li>
                <li>In connection with a merger, sale, or acquisition of all or a portion of our company</li>
              </ul>
            </section>

            <section>
              <h2 className="mb-3">7. Data Retention</h2>
              <p className="text-gray-700 leading-relaxed">
                We retain your personal information for as long as necessary to provide the Service and fulfill the purposes outlined in this Privacy Policy. You may request deletion of your data at any time by contacting us. Upon request, we will delete your data within 30 days, except where we are required to retain it for legal purposes.
              </p>
            </section>

            <section>
              <h2 className="mb-3">8. Your Rights and Choices</h2>
              <p className="text-gray-700 leading-relaxed mb-3">
                You have the following rights regarding your personal information:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-gray-700">
                <li><strong>Access:</strong> Request a copy of your personal data</li>
                <li><strong>Correction:</strong> Request correction of inaccurate data</li>
                <li><strong>Deletion:</strong> Request deletion of your personal data</li>
                <li><strong>Export:</strong> Request export of your data in a portable format</li>
                <li><strong>Withdraw Consent:</strong> Withdraw consent for data processing at any time</li>
              </ul>
            </section>

            <section>
              <h2 className="mb-3">9. Sensitive Information</h2>
              <p className="text-gray-700 leading-relaxed">
                <strong>Important:</strong> Personal Assistant is not designed for collecting, storing, or processing highly sensitive personal information such as health records, financial account numbers, social security numbers, or other regulated data types. Please do not record or store such information using the Service.
              </p>
            </section>

            <section>
              <h2 className="mb-3">10. Children's Privacy</h2>
              <p className="text-gray-700 leading-relaxed">
                The Service is not intended for children under the age of 13. We do not knowingly collect personal information from children under 13. If you believe we have collected information from a child under 13, please contact us immediately.
              </p>
            </section>

            <section>
              <h2 className="mb-3">11. International Data Transfers</h2>
              <p className="text-gray-700 leading-relaxed">
                Your information may be transferred to and processed in countries other than your country of residence. These countries may have different data protection laws. By using the Service, you consent to the transfer of your information to these countries.
              </p>
            </section>

            <section>
              <h2 className="mb-3">12. Changes to This Privacy Policy</h2>
              <p className="text-gray-700 leading-relaxed">
                We may update this Privacy Policy from time to time. We will notify you of any material changes by posting the new Privacy Policy on this page and updating the "Last updated" date. We encourage you to review this Privacy Policy periodically.
              </p>
            </section>

            <section>
              <h2 className="mb-3">13. Contact Us</h2>
              <p className="text-gray-700 leading-relaxed">
                If you have questions or concerns about this Privacy Policy or our data practices, please contact us at:
              </p>
              <p className="text-gray-700 leading-relaxed mt-2">
                Email: privacy@personalassistant.com<br />
                Address: [Your Company Address]
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
