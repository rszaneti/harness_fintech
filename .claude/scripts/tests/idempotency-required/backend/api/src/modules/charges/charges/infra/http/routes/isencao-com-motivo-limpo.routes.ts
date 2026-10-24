import { Router } from 'express'
import BtgWebhookController from '../controllers/BtgWebhookController'

const webhookRouter = Router()
const btgWebhookController = new BtgWebhookController()

// [BE-003] webhook público: registrado antes do ensureAuthenticated.
// idempotency-exempt: webhook do BTG — deduplicado por event_id (RN-REG-02)
webhookRouter.post(
  '/btg',
  btgWebhookController.create,
)

export default webhookRouter
