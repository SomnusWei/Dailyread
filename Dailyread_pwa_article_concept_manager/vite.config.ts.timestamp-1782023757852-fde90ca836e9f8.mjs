// vite.config.ts
import { defineConfig } from "file:///E:/item/DailyRead/Dailyread_pwa_article_concept_manager/node_modules/vite/dist/node/index.js";
import vue from "file:///E:/item/DailyRead/Dailyread_pwa_article_concept_manager/node_modules/@vitejs/plugin-vue/dist/index.mjs";
import { VitePWA } from "file:///E:/item/DailyRead/Dailyread_pwa_article_concept_manager/node_modules/vite-plugin-pwa/dist/index.js";
import { resolve } from "path";
var __vite_injected_original_dirname = "E:\\item\\DailyRead\\Dailyread_pwa_article_concept_manager";
var vite_config_default = defineConfig({
  plugins: [
    vue(),
    VitePWA({
      registerType: "autoUpdate",
      manifest: {
        name: "\u6BCF\u65E5\u9605\u8BFB\u7BA1\u7406\u5668",
        short_name: "\u6BCF\u65E5\u9605\u8BFB",
        description: "\u6587\u7AE0\u4E0E\u6982\u5FF5\u7BA1\u7406\u5DE5\u5177",
        start_url: "/",
        display: "standalone",
        background_color: "#ffffff",
        theme_color: "#4f46e5",
        icons: [
          { src: "icon-192.png", sizes: "192x192", type: "image/png" },
          { src: "icon-512.png", sizes: "512x512", type: "image/png" }
        ]
      },
      workbox: {
        globPatterns: ["**/*.{html,js,css,svg,png}"]
      }
    })
  ],
  resolve: {
    alias: {
      "@": resolve(__vite_injected_original_dirname, "src")
    }
  },
  server: {
    proxy: {
      // WebDAV 代理
      "/webdav": {
        target: "https://dav.jianguoyun.com",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/webdav/, "")
      },
      // 后端 API 代理
      "/api": {
        target: "http://localhost:3001",
        changeOrigin: true
      }
    }
  }
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcudHMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCJFOlxcXFxpdGVtXFxcXERhaWx5UmVhZFxcXFxEYWlseXJlYWRfcHdhX2FydGljbGVfY29uY2VwdF9tYW5hZ2VyXCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ZpbGVuYW1lID0gXCJFOlxcXFxpdGVtXFxcXERhaWx5UmVhZFxcXFxEYWlseXJlYWRfcHdhX2FydGljbGVfY29uY2VwdF9tYW5hZ2VyXFxcXHZpdGUuY29uZmlnLnRzXCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ltcG9ydF9tZXRhX3VybCA9IFwiZmlsZTovLy9FOi9pdGVtL0RhaWx5UmVhZC9EYWlseXJlYWRfcHdhX2FydGljbGVfY29uY2VwdF9tYW5hZ2VyL3ZpdGUuY29uZmlnLnRzXCI7aW1wb3J0IHsgZGVmaW5lQ29uZmlnIH0gZnJvbSAndml0ZSdcbmltcG9ydCB2dWUgZnJvbSAnQHZpdGVqcy9wbHVnaW4tdnVlJ1xuaW1wb3J0IHsgVml0ZVBXQSB9IGZyb20gJ3ZpdGUtcGx1Z2luLXB3YSdcbmltcG9ydCB7IHJlc29sdmUgfSBmcm9tICdwYXRoJ1xuXG5leHBvcnQgZGVmYXVsdCBkZWZpbmVDb25maWcoe1xuICBwbHVnaW5zOiBbXG4gICAgdnVlKCksXG4gICAgVml0ZVBXQSh7XG4gICAgICByZWdpc3RlclR5cGU6ICdhdXRvVXBkYXRlJyxcbiAgICAgIG1hbmlmZXN0OiB7XG4gICAgICAgIG5hbWU6ICdcdTZCQ0ZcdTY1RTVcdTk2MDVcdThCRkJcdTdCQTFcdTc0MDZcdTU2NjgnLFxuICAgICAgICBzaG9ydF9uYW1lOiAnXHU2QkNGXHU2NUU1XHU5NjA1XHU4QkZCJyxcbiAgICAgICAgZGVzY3JpcHRpb246ICdcdTY1ODdcdTdBRTBcdTRFMEVcdTY5ODJcdTVGRjVcdTdCQTFcdTc0MDZcdTVERTVcdTUxNzcnLFxuICAgICAgICBzdGFydF91cmw6ICcvJyxcbiAgICAgICAgZGlzcGxheTogJ3N0YW5kYWxvbmUnLFxuICAgICAgICBiYWNrZ3JvdW5kX2NvbG9yOiAnI2ZmZmZmZicsXG4gICAgICAgIHRoZW1lX2NvbG9yOiAnIzRmNDZlNScsXG4gICAgICAgIGljb25zOiBbXG4gICAgICAgICAgeyBzcmM6ICdpY29uLTE5Mi5wbmcnLCBzaXplczogJzE5MngxOTInLCB0eXBlOiAnaW1hZ2UvcG5nJyB9LFxuICAgICAgICAgIHsgc3JjOiAnaWNvbi01MTIucG5nJywgc2l6ZXM6ICc1MTJ4NTEyJywgdHlwZTogJ2ltYWdlL3BuZycgfVxuICAgICAgICBdXG4gICAgICB9LFxuICAgICAgd29ya2JveDoge1xuICAgICAgICBnbG9iUGF0dGVybnM6IFsnKiovKi57aHRtbCxqcyxjc3Msc3ZnLHBuZ30nXVxuICAgICAgfVxuICAgIH0pXG4gIF0sXG4gIHJlc29sdmU6IHtcbiAgICBhbGlhczoge1xuICAgICAgJ0AnOiByZXNvbHZlKF9fZGlybmFtZSwgJ3NyYycpXG4gICAgfVxuICB9LFxuICBzZXJ2ZXI6IHtcbiAgICBwcm94eToge1xuICAgICAgLy8gV2ViREFWIFx1NEVFM1x1NzQwNlxuICAgICAgJy93ZWJkYXYnOiB7XG4gICAgICAgIHRhcmdldDogJ2h0dHBzOi8vZGF2LmppYW5ndW95dW4uY29tJyxcbiAgICAgICAgY2hhbmdlT3JpZ2luOiB0cnVlLFxuICAgICAgICByZXdyaXRlOiAocGF0aCkgPT4gcGF0aC5yZXBsYWNlKC9eXFwvd2ViZGF2LywgJycpXG4gICAgICB9LFxuICAgICAgLy8gXHU1NDBFXHU3QUVGIEFQSSBcdTRFRTNcdTc0MDZcbiAgICAgICcvYXBpJzoge1xuICAgICAgICB0YXJnZXQ6ICdodHRwOi8vbG9jYWxob3N0OjMwMDEnLFxuICAgICAgICBjaGFuZ2VPcmlnaW46IHRydWVcbiAgICAgIH1cbiAgICB9XG4gIH1cbn0pXG4iXSwKICAibWFwcGluZ3MiOiAiO0FBQStWLFNBQVMsb0JBQW9CO0FBQzVYLE9BQU8sU0FBUztBQUNoQixTQUFTLGVBQWU7QUFDeEIsU0FBUyxlQUFlO0FBSHhCLElBQU0sbUNBQW1DO0FBS3pDLElBQU8sc0JBQVEsYUFBYTtBQUFBLEVBQzFCLFNBQVM7QUFBQSxJQUNQLElBQUk7QUFBQSxJQUNKLFFBQVE7QUFBQSxNQUNOLGNBQWM7QUFBQSxNQUNkLFVBQVU7QUFBQSxRQUNSLE1BQU07QUFBQSxRQUNOLFlBQVk7QUFBQSxRQUNaLGFBQWE7QUFBQSxRQUNiLFdBQVc7QUFBQSxRQUNYLFNBQVM7QUFBQSxRQUNULGtCQUFrQjtBQUFBLFFBQ2xCLGFBQWE7QUFBQSxRQUNiLE9BQU87QUFBQSxVQUNMLEVBQUUsS0FBSyxnQkFBZ0IsT0FBTyxXQUFXLE1BQU0sWUFBWTtBQUFBLFVBQzNELEVBQUUsS0FBSyxnQkFBZ0IsT0FBTyxXQUFXLE1BQU0sWUFBWTtBQUFBLFFBQzdEO0FBQUEsTUFDRjtBQUFBLE1BQ0EsU0FBUztBQUFBLFFBQ1AsY0FBYyxDQUFDLDRCQUE0QjtBQUFBLE1BQzdDO0FBQUEsSUFDRixDQUFDO0FBQUEsRUFDSDtBQUFBLEVBQ0EsU0FBUztBQUFBLElBQ1AsT0FBTztBQUFBLE1BQ0wsS0FBSyxRQUFRLGtDQUFXLEtBQUs7QUFBQSxJQUMvQjtBQUFBLEVBQ0Y7QUFBQSxFQUNBLFFBQVE7QUFBQSxJQUNOLE9BQU87QUFBQTtBQUFBLE1BRUwsV0FBVztBQUFBLFFBQ1QsUUFBUTtBQUFBLFFBQ1IsY0FBYztBQUFBLFFBQ2QsU0FBUyxDQUFDLFNBQVMsS0FBSyxRQUFRLGFBQWEsRUFBRTtBQUFBLE1BQ2pEO0FBQUE7QUFBQSxNQUVBLFFBQVE7QUFBQSxRQUNOLFFBQVE7QUFBQSxRQUNSLGNBQWM7QUFBQSxNQUNoQjtBQUFBLElBQ0Y7QUFBQSxFQUNGO0FBQ0YsQ0FBQzsiLAogICJuYW1lcyI6IFtdCn0K
