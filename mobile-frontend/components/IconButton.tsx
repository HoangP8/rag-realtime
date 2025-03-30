import { Text, StyleSheet, Pressable } from "react-native";
import MaterialIcons from "@expo/vector-icons/MaterialIcons";
type Prop = {
  icon: keyof typeof MaterialIcons.glyphMap;
  label: string;
  onPress: () => void;
};

export default function IconButton({ icon, label, onPress }: Prop) {
  return (
    <Pressable style={styles.iconButton}>
      <MaterialIcons name={icon} size={24} color="#fff" />
      <Text style={styles.iconButtonLabel}>{label}</Text>
    </Pressable>
  );
}
const styles = StyleSheet.create({
  iconButton: {
    justifyContent: "center",
    alignItems: "center",
  },
  iconButtonLabel: {
    color: "#fff",
    marginTop: 12,
  },
});
