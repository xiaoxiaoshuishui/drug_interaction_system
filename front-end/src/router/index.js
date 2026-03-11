import { createRouter, createWebHistory } from "vue-router";

const routes = [
  {
    path: "/",
    redirect: "/home",
  },
  {
    path: "/login",
    name: "Login",
    component: () => import("../views/Login.vue"),
    meta: {
      title: "登录",
      keepAlive: false,
    },
  },
  {
    path: "/register",
    name: "Register",
    component: () => import("../views/Register.vue"),
    meta: {
      title: "注册",
      keepAlive: false,
    },
  },
  {
    path: "/profile",
    name: "Profile",
    component: () => import("../views/Profile.vue"),
    meta: {
      title: "个人资料",
      keepAlive: false,
    },
  },
  {
    path: "/account",
    name: "Account",
    component: () => import("../views/Account.vue"),
    meta: {
      title: "账户设置",
      keepAlive: false,
    },
  },
  {
    path: "/home",
    name: "Home",
    redirect: "/home/dashboard",
    component: () => import("../views/Home.vue"),
    meta: {
      title: "首页",
      keepAlive: true,
    },
    children: [
      {
        path: "dashboard",
        name: "Dashboard",
        component: () => import("../views/Dashboard.vue"),
      },
      {
        path: "data",
        name: "Data",
        component: () => import("../views/Data.vue"),
      },
    ],
  },
  {
    path: "/ddi",
    name: "Ddi",
    redirect: "/ddi/prediction",
    component: () => import("../views/Home.vue"),
    meta: {
      title: "首页",
      keepAlive: true,
    },
    children: [
      {
        path: "prediction",
        name: "Prediction",
        component: () => import("../views/Prediction.vue"),
      },
      {
        path: "history",
        name: "History",
        component: () => import("../views/History.vue"),
      },
    ],
  },
  {
    path: "/dsa",
    name: "Dsa",
    redirect: "/dsa/sider",
    component: () => import("../views/Home.vue"),
    meta: {
      title: "首页",
      keepAlive: true,
    },
    children: [
      {
        path: "sider",
        name: "Sider",
        component: () => import("../views/Sider.vue"),
      },
      {
        path: "record",
        name: "Record",
        component: () => import("../views/Record.vue"),
      },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

// 全局前置守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  document.title = to.meta.title || "药物不良反应预测";

  // 直接允许访问所有页面
  next();
});

export default router;
