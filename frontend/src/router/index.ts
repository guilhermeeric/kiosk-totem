import { createRouter, createWebHistory } from 'vue-router'

import CartView from '../views/CartView.vue'
import CheckoutView from '../views/CheckoutView.vue'
import HandoffView from '../views/HandoffView.vue'
import KitchenView from '../views/KitchenView.vue'
import MenuView from '../views/MenuView.vue'
import ReceiptView from '../views/ReceiptView.vue'
import StartView from '../views/StartView.vue'
import TrackView from '../views/TrackView.vue'
import VisorView from '../views/VisorView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'start', component: StartView },
    { path: '/menu', name: 'menu', component: MenuView },
    { path: '/cart', name: 'cart', component: CartView },
    { path: '/checkout', name: 'checkout', component: CheckoutView },
    { path: '/receipt/:id', name: 'receipt', component: ReceiptView, props: true },
    { path: '/track/:id', name: 'track', component: TrackView, props: true },
    { path: '/handoff/:sessionId?', name: 'handoff', component: HandoffView },
    { path: '/kitchen', name: 'kitchen', component: KitchenView },
    { path: '/visor', name: 'visor', component: VisorView },
  ],
})

export default router
