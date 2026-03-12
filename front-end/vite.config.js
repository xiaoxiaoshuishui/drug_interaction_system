import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import Components from 'unplugin-vue-components/vite'
import { VantResolver } from 'unplugin-vue-components/resolvers'

export default defineConfig({
  plugins: [
    vue(),
    Components({
      // 指定组件存放目录
      dirs: ['src/components'],
      
      // 自动导入的组件解析器
      resolvers: [
        VantResolver({
          // 是否引入样式，默认true
          importStyle: true,
          
          // 是否引入es模块，默认true
          esModule: true,
          
          // 解决SSR问题
          ssr: false,
        })
      ],

      dts: false,
      
      // 在模板中自动导入组件
      deep: true,
      
      // 允许子目录中的组件
      allowOverrides: true,
      
      // 过滤不需要自动导入的组件
      exclude: [/[\\/]node_modules[\\/]/, /[\\/]\.git[\\/]/, /[\\/]\.nuxt[\\/]/],
    }),
  ],
})
