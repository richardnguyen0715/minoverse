// AnalyzeScreen — TODO: implement
import React from "react"
import { View, Text, StyleSheet } from "react-native"

export default function AnalyzeScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>AnalyzeScreen</Text>
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: "center", justifyContent: "center" },
  title: { fontSize: 24, fontWeight: "bold" },
})
