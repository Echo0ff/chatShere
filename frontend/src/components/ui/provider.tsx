"use client"

import { ChakraProvider } from "@chakra-ui/react"
import { system } from "../../theme"
import { ColorModeProvider, type ColorModeProviderProps } from "./color-mode"

export interface ProviderProps extends ColorModeProviderProps {
  children: React.ReactNode
}

export function Provider({ children, ...props }: ProviderProps) {
  return (
    <ChakraProvider value={system}>
      <ColorModeProvider defaultTheme="dark" enableSystem {...props}>
        {children}
      </ColorModeProvider>
    </ChakraProvider>
  )
} 