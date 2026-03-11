'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Check, Zap, Crown, ArrowRight } from 'lucide-react'

const plans = [
  {
    id: 'basic',
    name: 'Basic',
    price: 5,
    period: 'month',
    model: 'GPT-4o-mini',
    description: 'Perfect for casual users getting started with AI coaching',
    features: [
      'Daily AI-powered planning',
      'Career coaching chat',
      'Skill development tips',
      'Basic task tracking',
      'GPT-4o-mini responses',
      'Email support',
    ],
    cta: 'Start Basic',
    popular: false,
    icon: Zap,
    gradient: 'from-slate-600 to-slate-700',
  },
  {
    id: 'pro',
    name: 'Pro',
    price: 12,
    period: 'month',
    model: 'GPT-4o',
    description: 'For serious users who want the best AI coaching experience',
    features: [
      'Everything in Basic',
      'Advanced GPT-4o responses',
      'Priority response times',
      'Deep career analysis',
      'Weekly progress reports',
      'Voice chat support',
      'Custom goal frameworks',
      'Priority support',
    ],
    cta: 'Go Pro',
    popular: true,
    icon: Crown,
    gradient: 'from-sky-500 to-blue-600',
  },
]

export default function PricingPage() {
  const router = useRouter()
  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'yearly'>('monthly')
  const [loading, setLoading] = useState<string | null>(null)

  const getPrice = (basePrice: number) => {
    if (billingPeriod === 'yearly') {
      return Math.round(basePrice * 10) // 2 months free
    }
    return basePrice
  }

  const handleSelectPlan = async (planId: string) => {
    setLoading(planId)
    // Redirect to checkout page with plan and billing parameters
    router.push(`/checkout?plan=${planId}&billing=${billingPeriod}`)
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-900 to-slate-800">
      {/* Header */}
      <div className="pt-16 pb-12 text-center px-4">
        <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
          Choose Your Plan
        </h1>
        <p className="text-lg text-slate-400 max-w-2xl mx-auto">
          Unlock your potential with AI-powered career coaching and daily planning
        </p>

        {/* Billing Toggle */}
        <div className="mt-8 inline-flex items-center gap-3 bg-slate-800 p-1 rounded-full">
          <button
            onClick={() => setBillingPeriod('monthly')}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
              billingPeriod === 'monthly'
                ? 'bg-sky-500 text-white'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Monthly
          </button>
          <button
            onClick={() => setBillingPeriod('yearly')}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-all flex items-center gap-2 ${
              billingPeriod === 'yearly'
                ? 'bg-sky-500 text-white'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Yearly
            <span className="text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded-full">
              Save 17%
            </span>
          </button>
        </div>
      </div>

      {/* Pricing Cards */}
      <div className="max-w-5xl mx-auto px-4 pb-20">
        <div className="grid md:grid-cols-2 gap-8">
          {plans.map((plan) => {
            const Icon = plan.icon
            return (
              <div
                key={plan.id}
                className={`relative rounded-2xl p-8 ${
                  plan.popular
                    ? 'bg-gradient-to-b from-sky-500/10 to-blue-600/10 border-2 border-sky-500/50'
                    : 'bg-slate-800/50 border border-slate-700'
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                    <span className="bg-gradient-to-r from-sky-500 to-blue-600 text-white text-sm font-medium px-4 py-1 rounded-full">
                      Most Popular
                    </span>
                  </div>
                )}

                <div className="flex items-center gap-3 mb-4">
                  <div className={`p-2 rounded-lg bg-gradient-to-br ${plan.gradient}`}>
                    <Icon className="w-5 h-5 text-white" />
                  </div>
                  <h2 className="text-2xl font-bold text-white">{plan.name}</h2>
                </div>

                <div className="mb-4">
                  <span className="text-4xl font-bold text-white">
                    ${getPrice(plan.price)}
                  </span>
                  <span className="text-slate-400">
                    /{billingPeriod === 'yearly' ? 'year' : 'month'}
                  </span>
                </div>

                <p className="text-slate-400 mb-6">{plan.description}</p>

                <div className="mb-2 flex items-center gap-2">
                  <span className="text-xs text-slate-500 uppercase tracking-wide">
                    AI Model
                  </span>
                  <span className="text-sm font-medium text-sky-400 bg-sky-500/10 px-2 py-0.5 rounded">
                    {plan.model}
                  </span>
                </div>

                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature, i) => (
                    <li key={i} className="flex items-start gap-3">
                      <Check className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                      <span className="text-slate-300">{feature}</span>
                    </li>
                  ))}
                </ul>

                <button
                  onClick={() => handleSelectPlan(plan.id)}
                  disabled={loading === plan.id}
                  className={`w-full py-3 px-6 rounded-lg font-medium flex items-center justify-center gap-2 transition-all ${
                    plan.popular
                      ? 'bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-600 hover:to-blue-700 text-white'
                      : 'bg-slate-700 hover:bg-slate-600 text-white'
                  } disabled:opacity-50 disabled:cursor-not-allowed`}
                >
                  {loading === plan.id ? (
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    <>
                      {plan.cta}
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </div>
            )
          })}
        </div>

        {/* FAQ Section */}
        <div className="mt-20">
          <h2 className="text-2xl font-bold text-white text-center mb-8">
            Frequently Asked Questions
          </h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-slate-800/50 rounded-xl p-6">
              <h3 className="font-semibold text-white mb-2">
                What's the difference between GPT-4o-mini and GPT-4o?
              </h3>
              <p className="text-slate-400 text-sm">
                GPT-4o is OpenAI's most capable model with better reasoning, deeper insights,
                and more nuanced responses. GPT-4o-mini is faster and more affordable while
                still providing excellent coaching.
              </p>
            </div>
            <div className="bg-slate-800/50 rounded-xl p-6">
              <h3 className="font-semibold text-white mb-2">
                Can I switch plans anytime?
              </h3>
              <p className="text-slate-400 text-sm">
                Yes! You can upgrade or downgrade your plan at any time. When upgrading,
                you'll get immediate access to Pro features. Downgrades take effect at
                the next billing cycle.
              </p>
            </div>
            <div className="bg-slate-800/50 rounded-xl p-6">
              <h3 className="font-semibold text-white mb-2">
                Is there a free trial?
              </h3>
              <p className="text-slate-400 text-sm">
                We offer a 7-day free trial on the Pro plan so you can experience
                GPT-4o powered coaching before committing.
              </p>
            </div>
            <div className="bg-slate-800/50 rounded-xl p-6">
              <h3 className="font-semibold text-white mb-2">
                What payment methods do you accept?
              </h3>
              <p className="text-slate-400 text-sm">
                We accept all major credit cards (Visa, Mastercard, Amex) through
                our secure payment processor Stripe.
              </p>
            </div>
          </div>
        </div>

        {/* Back to Home */}
        <div className="mt-12 text-center">
          <button
            onClick={() => router.push('/')}
            className="text-slate-400 hover:text-white transition-colors"
          >
            ← Back to Home
          </button>
        </div>
      </div>
    </div>
  )
}
