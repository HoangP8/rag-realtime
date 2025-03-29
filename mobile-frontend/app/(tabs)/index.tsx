import { View, StyleSheet, Text } from "react-native";
import CircleLogo from "@/components/CircleLogo";

export default function home() {
  return (
    <View style={styles.container}>
      <CircleLogo size={100} />
      <Text style={styles.title}>Capstone</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#ffffff",
  },
  logoContainer: {},
  title: {
    color: "#000",
    fontSize: 32,
  },
});
