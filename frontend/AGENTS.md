<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

# 🎨 Armonitex Enterprise Design System Rules

### 🚫 MANUEL RENK KULLANIMI KESİNLİKLE YASAKTIR (STRICT AD-HOC COLOR BAN)
- Bileşenlerde doğrudan elle gri, siyah veya ad-hoc renk sınıfları (`bg-slate-900`, `text-slate-600`, `gray-*`, `black`) **KULLANILAMAZ**.
- Tüm renk ve stil işlemleri `src/app/globals.css` içerisinde tanımlı semantik token sınıfları (`.bg-white-token`, `.text-brand-token`, `.card-token`, `.btn-primary-token`) üzerinden yapılmalıdır.
- Referans ADR: `docs/adr/0007-design-system-tokens.md`.
