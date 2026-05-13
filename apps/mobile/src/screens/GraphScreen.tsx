// GraphScreen — TODO: implement
import React from "react"
import { View, Text, StyleSheet } from "react-native"

export default function GraphScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>GraphScreen</Text>
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: "center", justifyContent: "center" },
  title: { fontSize: 24, fontWeight: "bold" },
})
