import { createSystem, defaultConfig, defineConfig } from "@chakra-ui/react"

const config = defineConfig({
  theme: {
    semanticTokens: {
      colors: {
        bg: {
          DEFAULT: {
            value: { _light: "{colors.white}", _dark: "#0d1117" }
          },
          subtle: {
            value: { _light: "{colors.gray.50}", _dark: "#161b22" }
          },
          muted: {
            value: { _light: "{colors.gray.100}", _dark: "#21262d" }
          }
        },
        fg: {
          DEFAULT: {
            value: { _light: "{colors.black}", _dark: "#f0f6fc" }
          },
          muted: {
            value: { _light: "{colors.gray.600}", _dark: "#8b949e" }
          },
          subtle: {
            value: { _light: "{colors.gray.500}", _dark: "#6e7681" }
          }
        },
        border: {
          DEFAULT: {
            value: { _light: "{colors.gray.200}", _dark: "#30363d" }
          },
          muted: {
            value: { _light: "{colors.gray.100}", _dark: "#21262d" }
          }
        }
      }
    }
  }
})

export const system = createSystem(defaultConfig, config)
