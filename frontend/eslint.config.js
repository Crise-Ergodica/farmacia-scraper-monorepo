// https://docs.expo.dev/guides/using-eslint/
const { defineConfig } = require('eslint/config');
const expoConfig = require("eslint-config-expo/flat");

module.exports = defineConfig([
  expoConfig,
  {
    // Generated browser profiles, screenshots, and Expo export bundles are
    // validation artifacts, not application source files.
    ignores: ["dist/*", ".expo/**", ".expo-export-*/**", "reports/**"],
  }
]);
