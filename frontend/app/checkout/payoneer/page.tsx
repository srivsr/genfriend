'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { ArrowLeft, Copy, Check, Clock, Mail } from 'lucide-react'

const PAYONEER_EMAIL = process.env.NEXT_PUBLIC_PAYONEER_EMAIL || 'payments@srivsr.com'

export default function PayoneerPaymentPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const orderId = searchParams.get('order_id')

  const [order, setOrder] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [copied, setCopied] = useState(false)
  const [confirming, setConfirming] = useState(false)
  const [transactionId, setTransactionId] = useState('')

  useEffect(() => {
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
    } finally {
      setLoading(false)
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleConfirmPayment = async () => {
    if (!transactionId.trim()) {
      alert('Please enter the Payoneer transaction ID')
      return
    }

    setConfirming(true)
    try {
      const response = await fetch(
        `/api/v1/payment/payoneer/confirm?order_id=${orderId}&transaction_id=${transactionId}`,
        { method: 'POST' }
      )

      const data = await response.json()

      if (data.status === 'success') {
        router.push(`/checkout/success?order_id=${orderId}`)
      } else {
        alert('Failed to confirm payment. Please contact support.')
      }
    } catch (err) {
      alert('An error occurred. Please try again.')
    } finally {
      setConfirming(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-sky-500/30 border-t-sky-500 rounded-full animate-spin" />
      </div>
    )
  }

  if (!order) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 flex items-center justify-center">
        <div className="text-center">
          <p className="text-white text-xl mb-4">Order not found</p>
          <button
            onClick={() => router.push('/pricing')}
            className="text-sky-400 hover:text-sky-300"
          >
            Return to Pricing
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 py-12 px-4">
      <div className="max-w-2xl mx-auto">
        <button
          onClick={() => router.push('/pricing')}
          className="flex items-center gap-2 text-slate-400 hover:text-white mb-8 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Pricing
        </button>

        <div className="bg-slate-800/50 rounded-2xl p-8 border border-slate-700">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-12 h-12 bg-orange-500 rounded-full flex items-center justify-center">
              <span className="text-white font-bold text-xl">P</span>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Pay with Payoneer</h1>
              <p className="text-slate-400">Complete your payment via Payoneer</p>
            </div>
          </div>

          {/* Order Details */}
          <div className="bg-slate-900/50 rounded-xl p-4 mb-6">
            <div className="flex justify-between items-center mb-2">
              <span className="text-slate-400">Order ID</span>
              <span className="text-white font-mono">{order.order_id}</span>
            </div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-slate-400">Plan</span>
              <span className="text-white capitalize">{order.plan} ({order.billing_cycle})</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Amount</span>
              <span className="text-2xl font-bold text-white">
                ${order.amount} {order.currency}
              </span>
            </div>
          </div>

          {/* Payment Instructions */}
          <div className="space-y-4 mb-6">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <Mail className="w-5 h-5 text-sky-400" />
              Payment Instructions
            </h2>

            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-sky-500/20 text-sky-400 flex items-center justify-center text-sm flex-shrink-0 mt-0.5">
                  1
                </div>
                <p className="text-slate-300">
                  Log in to your <a href="https://payoneer.com" target="_blank" rel="noopener noreferrer" className="text-sky-400 hover:underline">Payoneer account</a>
                </p>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-sky-500/20 text-sky-400 flex items-center justify-center text-sm flex-shrink-0 mt-0.5">
                  2
                </div>
                <div className="text-slate-300">
                  <p>Send payment to:</p>
                  <div className="flex items-center gap-2 mt-1">
                    <code className="bg-slate-900 px-3 py-1 rounded text-sky-400">
                      {PAYONEER_EMAIL}
                    </code>
                    <button
                      onClick={() => copyToClipboard(PAYONEER_EMAIL)}
                      className="p-1 text-slate-400 hover:text-white transition-colors"
                    >
                      {copied ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-sky-500/20 text-sky-400 flex items-center justify-center text-sm flex-shrink-0 mt-0.5">
                  3
                </div>
                <div className="text-slate-300">
                  <p>Include this order ID in the payment note:</p>
                  <div className="flex items-center gap-2 mt-1">
                    <code className="bg-slate-900 px-3 py-1 rounded text-sky-400">
                      {order.order_id}
                    </code>
                    <button
                      onClick={() => copyToClipboard(order.order_id)}
                      className="p-1 text-slate-400 hover:text-white transition-colors"
                    >
                      <Copy className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-sky-500/20 text-sky-400 flex items-center justify-center text-sm flex-shrink-0 mt-0.5">
                  4
                </div>
                <p className="text-slate-300">
                  After payment, enter your Payoneer transaction ID below to confirm
                </p>
              </div>
            </div>
          </div>

          {/* Confirm Payment */}
          <div className="space-y-3">
            <label className="block text-sm text-slate-400">
              Payoneer Transaction ID
            </label>
            <input
              type="text"
              value={transactionId}
              onChange={(e) => setTransactionId(e.target.value)}
              placeholder="Enter your Payoneer transaction ID"
              className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
            />
            <button
              onClick={handleConfirmPayment}
              disabled={confirming || !transactionId.trim()}
              className="w-full bg-orange-500 hover:bg-orange-600 text-white font-medium py-3 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {confirming ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <Check className="w-5 h-5" />
                  Confirm Payment
                </>
              )}
            </button>
          </div>

          {/* Note */}
          <div className="mt-6 flex items-start gap-2 text-sm text-slate-400">
            <Clock className="w-4 h-4 mt-0.5 flex-shrink-0" />
            <p>
              Your subscription will be activated within 24 hours after we verify your payment.
              For immediate activation, please email us at support@srivsr.com with your transaction details.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
