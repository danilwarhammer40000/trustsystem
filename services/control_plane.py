async def process_successful_payment(user_id: str, plan: str, payment_id: str) -> None:
    try:
        logger.info(f"[WEBHOOK] payment={payment_id} user={user_id} plan={plan}")

        # 1. Идемпотентность
        if payment_id and is_paid(payment_id):
            logger.info(f"[SKIP] already processed {payment_id}")
            return

        # 🔥 ВАЖНО: фиксируем СРАЗУ
        if payment_id:
            mark_paid(payment_id)

        # 2. USER
        user = create_user_if_not_exists(user_id)

        # 3. План
        try:
            days = int(plan)
        except:
            logger.error(f"invalid plan: {plan}")
            return

        # 4. Продление
        updated_user = extend_user_by_tg(user_id, days)

        if not updated_user:
            logger.error(f"user not found after extend {user_id}")
            return

        username = updated_user.get("username")

        logger.info(f"[OK] extended {username} for {days} days")

        # 5. Sync
        try:
            full_sync()
            restart_trusttunnel()
        except Exception as e:
            logger.error(f"sync error: {e}")

        # 6. VPN
        card = build_vpn_card(username)

        try:
            await bot.send_message(
                chat_id=int(user_id),
                text=card["text"],
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"send failed: {e}")

        logger.info(f"[SUCCESS] payment done {payment_id}")

    except Exception as e:
        logger.exception(f"[CRITICAL] {payment_id}")