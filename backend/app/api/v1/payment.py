"""
Payment processing routes using PayPal and Payoneer
"""
import os
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.user import User
from sqlalchemy import select

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payment", tags=["payment"])


class CreateOrderRequest(BaseModel):
    plan: str  # 'basic' or 'pro'
    billing_cycle: str = "monthly"  # 'monthly' or 'yearly'
    customer_email: EmailStr
    customer_name: Optional[str] = None
    payment_method: str = "paypal"  # 'paypal' or 'payoneer'


class OrderResponse(BaseModel):
    order_id: str
    amount: float
    currency: str
    status: str
    plan: str
    billing_cycle: str
    payment_url: Optional[str] = None
    paypal_client_id: Optional[str] = None


class PaymentVerifyRequest(BaseModel):
    order_id: str
    payment_id: str
    payer_id: Optional[str] = None


# Pricing configuration for GenFriend
PRICING = {
    "basic": {
        "monthly": {
            "amount": 5.00,
            "currency": "USD",
            "description": "Gen-Friend Basic - Monthly",
            "model": "gpt-4o-mini"
        },
        "yearly": {
            "amount": 50.00,
            "currency": "USD",
            "description": "Gen-Friend Basic - Yearly (2 months free)",
            "model": "gpt-4o-mini"
        }
    },
    "pro": {
        "monthly": {
            "amount": 12.00,
            "currency": "USD",
            "description": "Gen-Friend Pro - Monthly",
            "model": "gpt-4o"
        },
        "yearly": {
            "amount": 120.00,
            "currency": "USD",
            "description": "Gen-Friend Pro - Yearly (2 months free)",
            "model": "gpt-4o"
        }
    }
}

# Payment configuration
PAYMENT_CONFIG = {
    "paypal_client_id": os.getenv("PAYPAL_CLIENT_ID"),
    "paypal_client_secret": os.getenv("PAYPAL_CLIENT_SECRET"),
    "paypal_mode": os.getenv("PAYPAL_MODE", "sandbox"),  # 'sandbox' or 'live'
    "payoneer_email": os.getenv("PAYONEER_EMAIL"),
    "payoneer_partner_id": os.getenv("PAYONEER_PARTNER_ID"),
    "base_url": os.getenv("BASE_URL", "https://genfriend.srivsr.com"),
}

# In-memory order storage (use database in production)
ORDERS_DB: Dict[str, Dict[str, Any]] = {}


def generate_order_id() -> str:
    return f"GF-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"


def get_paypal_api_url() -> str:
    if PAYMENT_CONFIG["paypal_mode"] == "live":
        return "https://api-m.paypal.com"
    return "https://api-m.sandbox.paypal.com"


@router.get("/plans")
async def get_pricing_plans():
    """Get available pricing plans"""
    plans = {}
    for plan_name, cycles in PRICING.items():
        plans[plan_name] = {
            "plan_id": plan_name,
            "monthly": {
                "amount": cycles["monthly"]["amount"],
                "currency": cycles["monthly"]["currency"],
                "description": cycles["monthly"]["description"],
                "model": cycles["monthly"]["model"],
                "price_display": f"${cycles['monthly']['amount']:.0f}/month"
            },
            "yearly": {
                "amount": cycles["yearly"]["amount"],
                "currency": cycles["yearly"]["currency"],
                "description": cycles["yearly"]["description"],
                "model": cycles["yearly"]["model"],
                "price_display": f"${cycles['yearly']['amount']:.0f}/year"
            }
        }
    return {
        "plans": plans,
        "payment_methods": ["paypal", "payoneer"]
    }


@router.post("/create-order", response_model=OrderResponse)
async def create_payment_order(request: CreateOrderRequest):
    """Create a payment order"""
    if request.plan not in PRICING:
        raise HTTPException(status_code=400, detail="Invalid plan")

    if request.billing_cycle not in ["monthly", "yearly"]:
        raise HTTPException(status_code=400, detail="Invalid billing cycle")

    plan_config = PRICING[request.plan][request.billing_cycle]
    order_id = generate_order_id()

    order = {
        "order_id": order_id,
        "customer_email": request.customer_email,
        "customer_name": request.customer_name,
        "plan": request.plan,
        "billing_cycle": request.billing_cycle,
        "amount": plan_config["amount"],
        "currency": plan_config["currency"],
        "description": plan_config["description"],
        "payment_method": request.payment_method,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
    }

    ORDERS_DB[order_id] = order
    logger.info(f"Created order: {order_id} for {request.customer_email}")

    response = OrderResponse(
        order_id=order_id,
        amount=plan_config["amount"],
        currency=plan_config["currency"],
        status="pending",
        plan=request.plan,
        billing_cycle=request.billing_cycle
    )

    if request.payment_method == "paypal":
        response.paypal_client_id = PAYMENT_CONFIG["paypal_client_id"]
    elif request.payment_method == "payoneer":
        response.payment_url = f"{PAYMENT_CONFIG['base_url']}/checkout/payoneer/{order_id}"

    return response


@router.get("/order/{order_id}")
async def get_order_status(order_id: str):
    """Get order status"""
    if order_id not in ORDERS_DB:
        raise HTTPException(status_code=404, detail="Order not found")

    order = ORDERS_DB[order_id]

    # Check if expired
    expires_at = datetime.fromisoformat(order["expires_at"])
    if order["status"] == "pending" and datetime.now() > expires_at:
        order["status"] = "expired"
        ORDERS_DB[order_id] = order

    return {
        "order_id": order["order_id"],
        "status": order["status"],
        "amount": order["amount"],
        "currency": order["currency"],
        "plan": order["plan"],
        "billing_cycle": order["billing_cycle"],
        "paid_at": order.get("paid_at")
    }


@router.post("/paypal/capture")
async def capture_paypal_payment(request: PaymentVerifyRequest, db: AsyncSession = Depends(get_db)):
    """Capture PayPal payment after approval"""
    if request.order_id not in ORDERS_DB:
        raise HTTPException(status_code=404, detail="Order not found")

    order = ORDERS_DB[request.order_id]

    if order["status"] == "paid":
        return {"status": "already_paid", "order_id": request.order_id}

    # In production, verify with PayPal API
    # import httpx
    # async with httpx.AsyncClient() as client:
    #     response = await client.post(
    #         f"{get_paypal_api_url()}/v2/checkout/orders/{request.payment_id}/capture",
    #         headers={"Authorization": f"Bearer {access_token}"}
    #     )

    order["status"] = "paid"
    order["paid_at"] = datetime.now().isoformat()
    order["paypal_payment_id"] = request.payment_id
    order["paypal_payer_id"] = request.payer_id
    order["payment_method"] = "paypal"

    ORDERS_DB[request.order_id] = order
    logger.info(f"PayPal payment captured for order: {request.order_id}")

    # Update user subscription
    await activate_subscription(db, order)

    return {"status": "success", "order_id": request.order_id}


@router.post("/payoneer/confirm")
async def confirm_payoneer_payment(
    order_id: str,
    transaction_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Confirm Payoneer payment (manual or webhook)"""
    if order_id not in ORDERS_DB:
        raise HTTPException(status_code=404, detail="Order not found")

    order = ORDERS_DB[order_id]

    if order["status"] == "paid":
        return {"status": "already_paid", "order_id": order_id}

    order["status"] = "paid"
    order["paid_at"] = datetime.now().isoformat()
    order["payoneer_transaction_id"] = transaction_id
    order["payment_method"] = "payoneer"

    ORDERS_DB[order_id] = order
    logger.info(f"Payoneer payment confirmed for order: {order_id}")

    # Update user subscription
    await activate_subscription(db, order)

    return {"status": "success", "order_id": order_id}


@router.post("/webhook/paypal")
async def paypal_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle PayPal webhook notifications"""
    try:
        payload = await request.json()
        event_type = payload.get("event_type")

        logger.info(f"PayPal webhook received: {event_type}")

        if event_type == "PAYMENT.CAPTURE.COMPLETED":
            resource = payload.get("resource", {})
            custom_id = resource.get("custom_id")  # Our order_id

            if custom_id and custom_id in ORDERS_DB:
                order = ORDERS_DB[custom_id]
                if order["status"] != "paid":
                    order["status"] = "paid"
                    order["paid_at"] = datetime.now().isoformat()
                    order["paypal_capture_id"] = resource.get("id")
                    order["payment_method"] = "paypal"
                    ORDERS_DB[custom_id] = order

                    await activate_subscription(db, order)
                    logger.info(f"Payment completed via webhook: {custom_id}")

        return {"status": "received"}
    except Exception as e:
        logger.error(f"PayPal webhook error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


async def activate_subscription(db: AsyncSession, order: Dict[str, Any]):
    """Activate user subscription after payment"""
    try:
        email = order["customer_email"]
        plan = order["plan"]
        billing_cycle = order["billing_cycle"]

        # Find user
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user:
            user.subscription_tier = plan
            user.subscription_status = "active"
            user.subscription_started_at = datetime.now()

            if billing_cycle == "monthly":
                user.subscription_ends_at = datetime.now() + timedelta(days=30)
            else:
                user.subscription_ends_at = datetime.now() + timedelta(days=365)

            user.monthly_message_count = 0
            user.message_count_reset_at = datetime.now()

            await db.commit()
            logger.info(f"Subscription activated for user: {email}, plan: {plan}")
        else:
            logger.warning(f"User not found for subscription activation: {email}")
    except Exception as e:
        logger.error(f"Failed to activate subscription: {e}")


@router.get("/config")
async def get_payment_config():
    """Get payment configuration for frontend"""
    return {
        "paypal_client_id": PAYMENT_CONFIG["paypal_client_id"],
        "paypal_mode": PAYMENT_CONFIG["paypal_mode"],
        "payoneer_email": PAYMENT_CONFIG["payoneer_email"],
        "supported_methods": ["paypal", "payoneer"],
        "currencies": ["USD"]
    }


# Admin endpoints
@router.get("/admin/orders")
async def list_orders(skip: int = 0, limit: int = 50):
    """List all orders (admin)"""
    orders = list(ORDERS_DB.values())
    orders.sort(key=lambda x: x["created_at"], reverse=True)
    return {
        "total": len(orders),
        "orders": orders[skip:skip+limit]
    }


@router.post("/admin/mark-paid/{order_id}")
async def mark_order_paid(order_id: str, db: AsyncSession = Depends(get_db)):
    """Manually mark order as paid (admin)"""
    if order_id not in ORDERS_DB:
        raise HTTPException(status_code=404, detail="Order not found")

    order = ORDERS_DB[order_id]
    order["status"] = "paid"
    order["paid_at"] = datetime.now().isoformat()
    order["payment_method"] = "manual"

    ORDERS_DB[order_id] = order

    await activate_subscription(db, order)

    return {"status": "success", "order_id": order_id}
