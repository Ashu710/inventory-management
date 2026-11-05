<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && backlogItem" class="modal-overlay" @click="close">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">
              {{ mode === 'view' ? t('purchaseOrder.viewTitle') : t('purchaseOrder.createTitle') }}
            </h3>
            <button class="close-button" @click="close" :aria-label="t('common.close')">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <!-- Backlog item summary (both modes) -->
            <div class="item-summary">
              <div class="item-name">{{ translateProductName(backlogItem.item_name) }}</div>
              <div class="item-sku">{{ t('purchaseOrder.sku') }}: {{ backlogItem.item_sku }}</div>
              <div class="info-grid">
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.orderId') }}</div>
                  <div class="info-value mono">{{ backlogItem.order_id }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.quantityNeeded') }}</div>
                  <div class="info-value">{{ t('purchaseOrder.units', { count: backlogItem.quantity_needed }) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.quantityAvailable') }}</div>
                  <div class="info-value">{{ t('purchaseOrder.units', { count: backlogItem.quantity_available }) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.shortage') }}</div>
                  <div class="info-value danger">{{ t('purchaseOrder.units', { count: shortage }) }}</div>
                </div>
              </div>
            </div>

            <!-- View mode -->
            <template v-if="mode === 'view'">
              <div v-if="loadingPO" class="state-text">{{ t('purchaseOrder.loading') }}</div>
              <div v-else-if="errorMessage" class="error-message">{{ errorMessage }}</div>
              <div v-else-if="purchaseOrder" class="info-grid po-details">
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.poId') }}</div>
                  <div class="info-value mono">{{ purchaseOrder.id }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.status') }}</div>
                  <div class="info-value"><span class="status-badge">{{ purchaseOrder.status }}</span></div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.supplier') }}</div>
                  <div class="info-value">{{ purchaseOrder.supplier_name }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.quantity') }}</div>
                  <div class="info-value">{{ t('purchaseOrder.units', { count: purchaseOrder.quantity }) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.unitCost') }}</div>
                  <div class="info-value">{{ money(purchaseOrder.unit_cost) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.total') }}</div>
                  <div class="info-value strong">{{ money(purchaseOrder.quantity * purchaseOrder.unit_cost) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.expectedDelivery') }}</div>
                  <div class="info-value">{{ formatDate(purchaseOrder.expected_delivery_date) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.createdDate') }}</div>
                  <div class="info-value">{{ formatDate(purchaseOrder.created_date) }}</div>
                </div>
                <div v-if="purchaseOrder.notes" class="info-item full-width">
                  <div class="info-label">{{ t('purchaseOrder.notes') }}</div>
                  <div class="info-value">{{ purchaseOrder.notes }}</div>
                </div>
              </div>
            </template>

            <!-- Create mode -->
            <form v-else id="po-form" class="po-form" @submit.prevent="submit" novalidate>
              <div class="form-field">
                <label for="po-supplier">{{ t('purchaseOrder.supplier') }} *</label>
                <input id="po-supplier" v-model="form.supplier_name" type="text" maxlength="120" />
              </div>
              <div class="form-row">
                <div class="form-field">
                  <label for="po-quantity">{{ t('purchaseOrder.quantity') }} *</label>
                  <input id="po-quantity" v-model.number="form.quantity" type="number" min="1" step="1" />
                </div>
                <div class="form-field">
                  <label for="po-unit-cost">{{ t('purchaseOrder.unitCost') }} (USD) *</label>
                  <input id="po-unit-cost" v-model.number="form.unit_cost" type="number" min="0" step="0.01" />
                </div>
              </div>
              <div class="form-field">
                <label for="po-date">{{ t('purchaseOrder.expectedDelivery') }} *</label>
                <input id="po-date" v-model="form.expected_delivery_date" type="date" />
              </div>
              <div class="form-field">
                <label for="po-notes">{{ t('purchaseOrder.notes') }}</label>
                <textarea id="po-notes" v-model="form.notes" rows="3" :placeholder="t('purchaseOrder.notesPlaceholder')"></textarea>
              </div>
              <div class="total-row">
                <span class="info-label">{{ t('purchaseOrder.total') }}</span>
                <span class="total-value">{{ money(total) }}</span>
              </div>
              <ul v-if="validationErrors.length && touched" class="validation-list">
                <li v-for="msg in validationErrors" :key="msg">{{ msg }}</li>
              </ul>
              <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>
            </form>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn-secondary" @click="close">{{ t('common.close') }}</button>
            <button
              v-if="mode !== 'view'"
              type="submit"
              form="po-form"
              class="btn-primary"
              :disabled="saving || !isValid"
            >
              {{ saving ? t('purchaseOrder.saving') : t('purchaseOrder.submit') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script>
import { ref, reactive, computed, watch } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrencyWithDecimals } from '../utils/currency'

export default {
  name: 'PurchaseOrderModal',
  props: {
    isOpen: { type: Boolean, default: false },
    backlogItem: { type: Object, default: null },
    mode: { type: String, default: 'create', validator: (v) => ['create', 'view'].includes(v) }
  },
  emits: ['close', 'po-created'],
  setup(props, { emit }) {
    const { t, currentCurrency, translateProductName } = useI18n()

    const form = reactive({
      supplier_name: '',
      quantity: 1,
      unit_cost: 0,
      expected_delivery_date: '',
      notes: ''
    })
    const saving = ref(false)
    const loadingPO = ref(false)
    const errorMessage = ref('')
    const purchaseOrder = ref(null)
    const touched = ref(false)

    const shortage = computed(() => {
      if (!props.backlogItem) return 0
      return Math.max(props.backlogItem.quantity_needed - props.backlogItem.quantity_available, 0)
    })

    const total = computed(() => (Number(form.quantity) || 0) * (Number(form.unit_cost) || 0))

    const validationErrors = computed(() => {
      const errs = []
      if (!form.supplier_name.trim()) errs.push(t('purchaseOrder.validation.supplierRequired'))
      if (!(Number(form.quantity) > 0)) errs.push(t('purchaseOrder.validation.quantityInvalid'))
      // v-model.number yields '' for an empty field, so check for a real number >= 0
      if (form.unit_cost === '' || !(Number(form.unit_cost) >= 0)) errs.push(t('purchaseOrder.validation.unitCostInvalid'))
      if (!form.expected_delivery_date) errs.push(t('purchaseOrder.validation.dateRequired'))
      return errs
    })
    const isValid = computed(() => validationErrors.value.length === 0)

    const money = (amount) => formatCurrencyWithDecimals(Number(amount) || 0, currentCurrency.value, 2)

    const formatDate = (value) => {
      if (!value) return '-'
      const d = new Date(value)
      // Guard against unparseable dates from the API
      if (isNaN(d.getTime())) return value
      return d.toLocaleDateString(currentCurrency.value === 'JPY' ? 'ja-JP' : 'en-US', {
        year: 'numeric', month: 'short', day: 'numeric'
      })
    }

    const extractError = (err, fallback) => err?.response?.data?.detail
      ? (typeof err.response.data.detail === 'string' ? err.response.data.detail : fallback)
      : fallback

    const resetForm = () => {
      form.supplier_name = ''
      // Default to the outstanding shortage; user can adjust
      form.quantity = Math.max(shortage.value, 1)
      form.unit_cost = 0
      form.expected_delivery_date = ''
      form.notes = ''
      touched.value = false
      errorMessage.value = ''
      saving.value = false
    }

    const loadPO = async () => {
      loadingPO.value = true
      errorMessage.value = ''
      purchaseOrder.value = null
      try {
        purchaseOrder.value = await api.getPurchaseOrderByBacklogItem(props.backlogItem.id)
      } catch (err) {
        errorMessage.value = extractError(err, t('purchaseOrder.loadError'))
        console.error('Failed to load purchase order:', err)
      } finally {
        loadingPO.value = false
      }
    }

    // Reinitialise every time the modal opens (or the target item/mode changes while open)
    watch(
      () => [props.isOpen, props.mode, props.backlogItem?.id],
      () => {
        if (!props.isOpen || !props.backlogItem) return
        errorMessage.value = ''
        if (props.mode === 'view') {
          loadPO()
        } else {
          resetForm()
        }
      },
      { immediate: true }
    )

    const submit = async () => {
      touched.value = true
      if (saving.value || !isValid.value) return
      saving.value = true
      errorMessage.value = ''
      try {
        const created = await api.createPurchaseOrder({
          backlog_item_id: props.backlogItem.id,
          supplier_name: form.supplier_name.trim(),
          quantity: Number(form.quantity),
          unit_cost: Number(form.unit_cost),
          expected_delivery_date: form.expected_delivery_date,
          notes: form.notes.trim() || null
        })
        emit('po-created', created)
      } catch (err) {
        // Backend returns 400/404/409 with a `detail` message
        errorMessage.value = extractError(err, t('purchaseOrder.createError'))
        console.error('Failed to create purchase order:', err)
      } finally {
        saving.value = false
      }
    }

    const close = () => emit('close')

    return {
      t, translateProductName, form, saving, loadingPO, errorMessage, purchaseOrder, touched,
      shortage, total, validationErrors, isValid, money, formatDate, submit, close
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 1rem;
}

.modal-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.15);
  max-width: 640px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.close-button {
  background: none;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 0.5rem;
  display: flex;
  border-radius: 6px;
  transition: all 0.15s ease;
}

.close-button:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem 2rem;
}

.item-summary {
  padding-bottom: 1.25rem;
  margin-bottom: 1.25rem;
  border-bottom: 1px solid #e2e8f0;
}

.item-name {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
}

.item-sku {
  font-size: 0.813rem;
  color: #64748b;
  font-family: 'Monaco', 'Courier New', monospace;
  margin: 0.25rem 0 1rem;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 1rem 1.5rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.info-item.full-width {
  grid-column: 1 / -1;
}

.info-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.info-value {
  font-size: 0.938rem;
  color: #0f172a;
  font-weight: 500;
}

.info-value.mono {
  font-family: 'Monaco', 'Courier New', monospace;
  color: #2563eb;
}

.info-value.danger {
  color: #dc2626;
}

.info-value.strong {
  font-weight: 700;
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  border-radius: 6px;
  background: #dbeafe;
  color: #1e40af;
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: capitalize;
}

.po-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.form-field label {
  font-size: 0.813rem;
  font-weight: 600;
  color: #334155;
}

.form-field input,
.form-field textarea {
  padding: 0.625rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.875rem;
  font-family: inherit;
  color: #0f172a;
  background: white;
}

.form-field input:focus,
.form-field textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}

.total-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.875rem 1rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}

.total-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
}

.validation-list {
  margin: 0;
  padding-left: 1.25rem;
  font-size: 0.813rem;
  color: #92400e;
}

.error-message {
  padding: 0.75rem 1rem;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #991b1b;
  font-size: 0.875rem;
}

.state-text {
  color: #64748b;
  font-size: 0.875rem;
  padding: 0.5rem 0;
}

.po-details {
  margin-top: 0.25rem;
}

.modal-footer {
  padding: 1.25rem 1.5rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.btn-secondary,
.btn-primary {
  padding: 0.625rem 1.25rem;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-secondary {
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  color: #334155;
}

.btn-secondary:hover {
  background: #e2e8f0;
  border-color: #cbd5e1;
}

.btn-primary {
  background: #0f172a;
  border: 1px solid #0f172a;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #1e293b;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Modal transition animations */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform 0.2s ease;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.95);
}
</style>
