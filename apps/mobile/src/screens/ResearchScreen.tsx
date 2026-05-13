// ResearchScreen — TODO: implement
import React from "react"
import { View, Text, StyleSheet } from "react-native"

export default function ResearchScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>ResearchScreen</Text>
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: "center", justifyContent: "center" },
  title: { fontSize: 24, fontWeight: "bold" },
})
