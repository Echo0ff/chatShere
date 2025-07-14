"use client"

// import { createContext, useContext } from "react" // 暂时未使用
import { ThemeProvider, useTheme } from "next-themes"
import { Button } from "@chakra-ui/react"

export interface ColorModeProviderProps {
  children: React.ReactNode
  defaultTheme?: string
  enableSystem?: boolean
}

export function ColorModeProvider({
  children,
  defaultTheme = "dark",
  enableSystem = true
}: ColorModeProviderProps) {
  return (
    <ThemeProvider
      attribute="class"
      defaultTheme={defaultTheme}
      enableSystem={enableSystem}
      disableTransitionOnChange
    >
      {children}
    </ThemeProvider>
  )
}

export function useColorMode() {
  const { theme, setTheme, systemTheme } = useTheme()

  const colorMode = theme === "system" ? systemTheme : theme

  return {
    colorMode,
    setColorMode: setTheme,
    toggleColorMode: () => {
      setTheme(colorMode === "dark" ? "light" : "dark")
    }
  }
}

export function useColorModeValue<T>(light: T, dark: T): T {
  const { colorMode } = useColorMode()
  return colorMode === "dark" ? dark : light
}

export function ColorModeButton() {
  const { colorMode, toggleColorMode } = useColorMode()

  return (
    <Button
      onClick={toggleColorMode}
      variant="ghost"
      size="sm"
      aria-label="切换主题"
    >
      {colorMode === "dark" ? "☀️" : "🌙"}
    </Button>
  )
}
