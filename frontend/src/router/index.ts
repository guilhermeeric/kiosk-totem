import { createRouter, createWebHistory } from 'vue-router'

import CartView from '../views/CartView.vue'
import CheckoutView from '../views/CheckoutView.vue'
import MenuView from '../views/MenuView.vue'
import ReceiptView from '../views/ReceiptView.vue'
import StartView from '../views/StartView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'start', component: StartView },
    { path: '/menu', name: 'menu', component: MenuView },
    { path: '/cart', name: 'cart', component: CartView },
    { path: '/checkout', name: 'checkout', component: CheckoutView },
    { path: '/receipt/:id', name: 'receipt', component: ReceiptView, props: true },
  ],
})

export default router
