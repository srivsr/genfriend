'use client'

import { useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { CheckCircle, ArrowRight, Sparkles } from 'lucide-react'
import confetti from 'canvas-confetti'

export default function PaymentSuccessPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const orderId = searchParams.get('order_id')

  const [order, setOrder] = useState<any>(null)

  useEffect(() => {
    // Trigger confetti
    confetti({
      particleCount: 100,
      spread: 70,
      origin: { y: 0.6 },
    })

    if (orderId) {
      fetchOrder()
    }
  }, [orderId])

  const fetchOrder = async () => {
    try {
      const response = await fetch(`/api/v1/payment/order/${orderId}`)
      const data = await response.json()
      setOrder(data)
    } catch (err) {
      console.error('Failed to fetch order:', err)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center">
        {/* Success Icon */}
        <div className="mb-8">
          <div className="w-24 h-24 mx-auto bg-green-500/20 rounded-full flex items-center justify-center mb-6 animate-bounce">
            <CheckCircle className="w-12 h-12 text-green-400" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">Payment Successful!</h1>
          <p className="text-slate-400">
            Thank you for subscribing to Gen-Friend
          </p>
        </div>

        {/* Order Details */}
        {order && (
          <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700 mb-8 text-left">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-yellow-400" />
              Your Subscription
            </h2>

            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-slate-400">Plan</span>
                <span className="text-white capitalize font-medium">
                  {order.plan} ({order.billing_cycle})
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Order ID</span>
                <span className="text-slate-300 font-mono text-sm">{order.order_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Amount Paid</span>
                <span className="text-white font-medium">
                  ${order.amount} {order.currency}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Status</span>
                <span className="text-green-400 font-medium capitalize">{order.status}</span>
              </div>
            </div>
          </div>
        )}

        {/* What's Next */}
        <div className="bg-sky-500/10 rounded-xl p-6 border border-sky-500/20 mb-8 text-left">
          <h3 className="text-white font-semibold mb-3">What's Next?</h3>
          <ul className="space-y-2 text-sm text-slate-300">
            <li className="flex items-start gap-2">
              <CheckCircle className="w-4 h-4 text-sky-400 mt-0.5 flex-shrink-0" />
              Your subscription is now active
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="w-4 h-4 text-sky-400 mt-0.5 flex-shrink-0" />
              Access all premium features immediately
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="w-4 h-4 text-sky-400 mt-0.5 flex-shrink-0" />
              A confirmation email has been sent to you
            </li>
          </ul>
        </div>

        {/* CTA */}
        <button
          onClick={() => router.push('/home')}
          className="w-full bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-600 hover:to-blue-700 text-white font-medium py-4 rounded-lg transition-all flex items-center justify-center gap-2"
        >
          Start Using Gen-Friend
          <ArrowRight className="w-5 h-5" />
        </button>

        <p className="mt-4 text-sm text-slate-500">
          Need help? Contact us at support@srivsr.com
        </p>
      </div>
    </div>
  )
}
