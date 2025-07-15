import { defineConfig } from "vite";
import path from "path";
import fsExtra from 'fs-extra';

export default defineConfig({
  build: {
    rollupOptions: {
      input: {
        content: path.resolve(__dirname, "src/content-script.ts"),
        popup: path.resolve(__dirname, "src/popup.ts")
      },
      output: {
        assetFileNames: 'assets/[name].[hash][extname]',
        chunkFileNames: 'assets/[name].[hash].js',
        entryFileNames: 'assets/[name].[hash].js'
      }
    },
    outDir: "dist",
    emptyOutDir: true
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src")
    }
  },
  plugins: [
    {
      name: 'copy-assets',
      async buildStart() {
        // Copy icons from public to dist
        const icons = ['icon16.png', 'icon32.png', 'icon48.png', 'icon128.png'];
        for (const icon of icons) {
          const source = path.resolve(__dirname, 'public', icon);
          const dest = path.resolve(__dirname, 'dist', icon);
          await fsExtra.copy(source, dest);
        }
      }
    },
    {
      name: 'copy-manifest',
      closeBundle() {
        fsExtra.copySync('manifest.json', 'dist/manifest.json');
      }
    }
  ]
});
