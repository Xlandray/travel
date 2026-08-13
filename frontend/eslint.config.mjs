import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
  {
    // Ten pages used to carry their own copy of the API base URL and five more
    // read the environment variable straight, which is how server-rendered
    // pages ended up calling a browser-only URL and silently getting nothing
    // back. `src/lib/api.ts` is now the only place allowed to decide this.
    files: ["src/**/*.{ts,tsx}"],
    ignores: ["src/lib/api.ts"],
    rules: {
      "no-restricted-syntax": [
        "error",
        {
          selector:
            "MemberExpression[object.object.name='process'][object.property.name='env'][property.name=/^(NEXT_PUBLIC_API_URL|INTERNAL_API_URL)$/]",
          message:
            "Use apiFetch()/apiBase() from @/lib/api. NEXT_PUBLIC_API_URL holds the URL a browser should use and is wrong on the server, which is how server-rendered pages ended up fetching nothing.",
        },
        {
          selector: ":matches(VariableDeclarator, FunctionDeclaration)[id.name='getApiBase']",
          message: "There is one API base, in @/lib/api. Import it rather than redefining it.",
        },
      ],
    },
  },
]);

export default eslintConfig;
