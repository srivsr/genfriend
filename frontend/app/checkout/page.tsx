'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { ArrowLeft, CreditCard, Shield, Check } from 'lucide-react'

interface Plan {
  name: string
  price: number
  billing: string
  model: string
  features: string[]
}

const PLANS: Record<string, Record<string, Plan>> = {
  basic: {
    monthly: {
      name: 'Basic',
      price: 5,
      billing: 'month',
      model: 'GPT-4o-mini',
      features: [
        'Daily AI-powered planning',
        'Career coaching chat',
        'Skill development tips',
        '500 messages/month',
      ],
    },
    yearly: {
      name: 'Basic',
      price: 50,
      billing: 'year',
      model: 'GPT-4o-mini',
      features: [
        'Daily AI-powered planning',
        'Career coaching chat',
        'Skill development tips',
        '500 messages/month',
        '2 months free',
      ],
    },
  },
  pro: {
    monthly: {
      name: 'Pro',
      price: 12,
      billing: 'month',
      model: 'GPT-4o',
      features: [
        'Everything in Basic',
        'Advanced GPT-4o responses',
        'Priority support',
        '2000 messages/month',
      ],
    },
    yearly: {
      name: 'Pro',
      price: 120,
      billing: 'year',
      model: 'GPT-4o',
      features: [
        'Everything in Basic',
        'Advanced GPT-4o responses',
        'Priority support',
        '2000 messages/month',
        '2 months free',
      ],
    },
  },
}

export default function CheckoutPage() {
  const router = useRouter()
  const searchParams = useSearchParams()

  const planId = searchParams.get('plan') || 'basic'
  const billingCycle = searchParams.get('billing') || 'monthly'

  const [email, setEmail] = useState('')
  const [name, setName] = useState('')
  const [paymentMethod, setPaymentMethod] = useState<'paypal' | 'payoneer'>('paypal')
  const [loading, setLoading] = useState(false)
  const [orderId, setOrderId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const plan = PLANS[planId]?.[billingCycle] || PLANS.basic.monthly

  const handleCreateOrder = async () => {
    if (!email) {
      setError('Please enter your email')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await fetch('/api/v1/payment/create-order', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          plan: planId,
          billing_cycle: billingCycle,
          customer_email: email,
          customer_name: name,
          payment_method: paymentMethod,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to create order')
      }

      setOrderId(data.order_id)

      if (paymentMethod === 'payoneer') {
        // Show Payoneer payment instructions
        router.push(`/checkout/payoneer?order_id=${data.order_id}`)
      }
      // For PayPal, render the PayPal button
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handlePayPalApprove = async (paypalOrderId: string, payerId: string) => {
    try {
      const response = await fetch('/api/v1/payment/paypal/capture', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          order_id: orderId,
          payment_id: paypalOrderId,
          payer_id: payerId,
        }),
      })

      const data = await response.json()

      if (data.status === 'success' || data.status === 'already_paid') {
        router.push('/checkout/success?order_id=' + orderId)
      } else {
        setError('Payment verification failed')
      }
    } catch (err: any) {
      setError(err.message)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Back Button */}
        <button
          onClick={() => router.push('/pricing')}
          className="flex items-center gap-2 text-slate-400 hover:text-white mb-8 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Pricing
        </button>

        <div className="grid md:grid-cols-2 gap-8">
          {/* Order Summary */}
          <div className="bg-slate-800/50 rounded-2xl p-6 border border-slate-700 h-fit">
            <h2 className="text-xl font-semibold text-white mb-6">Order Summary</h2>

            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-white font-medium">Gen-Friend {plan.name}</p>
                  <p className="text-sm text-slate-400">{plan.model} • Billed {plan.billing}ly</p>
                </div>
                <p className="text-2xl font-bold text-white">${plan.price}</p>
              </div>

              <hr className="border-slate-700" />

              <ul className="space-y-2">
                {plan.features.map((feature, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm text-slate-300">
                    <Check className="w-4 h-4 text-green-400" />
                    {feature}
                  </li>
                ))}
              </ul>

              <hr className="border-slate-700" />

              <div className="flex justify-between items-center">
                <p className="text-slate-400">Total</p>
                <p className="text-2xl font-bold text-white">
                  ${plan.price}
                  <span className="text-sm text-slate-400 font-normal">/{plan.billing}</span>
                </p>
              </div>
            </div>

            <div className="mt-6 flex items-center gap-2 text-sm text-slate-400">
              <Shield className="w-4 h-4" />
              <span>Secure payment processing</span>
            </div>
          </div>

          {/* Payment Form */}
          <div className="bg-slate-800/50 rounded-2xl p-6 border border-slate-700">
            <h2 className="text-xl font-semibold text-white mb-6">Payment Details</h2>

            {error && (
              <div className="mb-4 p-3 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400 text-sm">
                {error}
              </div>
            )}

            <div className="space-y-4">
              {/* Email */}
              <div>
                <label className="block text-sm text-slate-400 mb-1">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
                />
              </div>

              {/* Name */}
              <div>
                <label className="block text-sm text-slate-400 mb-1">Name (optional)</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Your name"
                  className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
                />
              </div>

              {/* Payment Method */}
              <div>
                <label className="block text-sm text-slate-400 mb-2">Payment Method</label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    onClick={() => setPaymentMethod('paypal')}
                    className={`p-4 rounded-lg border-2 transition-all flex flex-col items-center gap-2 ${
                      paymentMethod === 'paypal'
                        ? 'border-sky-500 bg-sky-500/10'
                        : 'border-slate-700 hover:border-slate-600'
                    }`}
                  >
                    <svg className="w-8 h-8" viewBox="0 0 24 24" fill="currentColor">
                      <path
                        d="M7.076 21.337H2.47a.641.641 0 0 1-.633-.74L4.944 3.72a.77.77 0 0 1 .757-.641h6.727c2.233 0 3.944.612 5.088 1.819.538.566.916 1.201 1.123 1.888.214.705.255 1.505.122 2.378l-.012.069v.406l.318.182c.268.154.508.337.714.549.283.288.497.624.636 1.003.144.392.21.853.196 1.369-.016.595-.116 1.14-.298 1.622-.2.528-.477.981-.826 1.346a3.755 3.755 0 0 1-1.252.862c-.474.21-1.009.361-1.593.45a9.588 9.588 0 0 1-1.553.121H13.82a.983.983 0 0 0-.97.826l-.014.085-.524 3.318-.012.062a.126.126 0 0 1-.125.107H7.076z"
                        fill="#253B80"
                      />
                    </svg>
                    <span className="text-sm text-white">PayPal</span>
                  </button>

                  <button
                    onClick={() => setPaymentMethod('payoneer')}
                    className={`p-4 rounded-lg border-2 transition-all flex flex-col items-center gap-2 ${
                      paymentMethod === 'payoneer'
                        ? 'border-sky-500 bg-sky-500/10'
                        : 'border-slate-700 hover:border-slate-600'
                    }`}
                  >
                    <div className="w-8 h-8 bg-orange-500 rounded-full flex items-center justify-center">
                      <span className="text-white font-bold text-sm">P</span>
                    </div>
                    <span className="text-sm text-white">Payoneer</span>
                  </button>
                </div>
              </div>

              {/* Submit Button */}
              {!orderId ? (
                <button
                  onClick={handleCreateOrder}
                  disabled={loading || !email}
                  className="w-full mt-4 bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-600 hover:to-blue-700 text-white font-medium py-4 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    <>
                      <CreditCard className="w-5 h-5" />
                      Continue to Payment
                    </>
                  )}
                </button>
              ) : paymentMethod === 'paypal' ? (
                <div className="mt-4">
                  <p className="text-sm text-slate-400 mb-3">Order created. Click below to pay with PayPal:</p>
                  <PayPalButton
                    amount={plan.price}
                    orderId={orderId}
                    onApprove={handlePayPalApprove}
                  />
                </div>
              ) : null}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function PayPalButton({
  amount,
  orderId,
  onApprove,
}: {
  amount: number
  orderId: string
  onApprove: (paypalOrderId: string, payerId: string) => void
}) {
  useEffect(() => {
    // Load PayPal SDK
    const script = document.createElement('script')
    script.src = `https://www.paypal.com/sdk/js?client-id=${process.env.NEXT_PUBLIC_PAYPAL_CLIENT_ID}&currency=USD`
    script.async = true
    script.onload = () => {
      if ((window as any).paypal) {
        ;(window as any).paypal
          .Buttons({
            createOrder: (_data: any, actions: any) => {
              return actions.order.create({
                purchase_units: [
                  {
                    amount: {
                      value: amount.toString(),
                    },
                    custom_id: orderId,
                  },
                ],
              })
            },
            onApprove: async (data: any) => {
              onApprove(data.orderID, data.payerID)
            },
            onError: (err: any) => {
              console.error('PayPal error:', err)
            },
          })
          .render('#paypal-button-container')
      }
    }
    document.body.appendChild(script)

    return () => {
      document.body.removeChild(script)
    }
  }, [amount, orderId, onApprove])

  return (
    <div
      id="paypal-button-container"
      className="min-h-[50px] flex items-center justify-center"
    />
  )
}
