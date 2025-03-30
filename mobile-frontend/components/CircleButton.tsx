import { View, StyleSheet, Pressable } from "react-native";
import MaterialIcon from "@expo/vector-icons/MaterialIcons";
import { useState } from "react";
type Prop = {
  onPress?: () => void;
  type: string;
};

export default function CircleButton({ onPress, type }: Prop) {
  const [pressed, setPressed] = useState(false);
  return (
    <View style={styles.circleButtonContainer}>
      <Pressable
        onPressIn={() => setPressed(true)}
        onPressOut={() => setPressed(false)}
        style={({ pressed }) => [
          styles.circleButton,
          pressed ? styles.buttonSmall : styles.buttonLarge,
        ]}
        onPress={onPress}
      >
        <MaterialIcon
          name={type === "audio" ? "multitrack-audio" : "arrow-upward"}
          size={20}
          color="#fff"
        />
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  circleButtonContainer: {
    justifyContent: "center",
    alignItems: "center",
    width: 30,
    height: 30,
    borderRadius: 15,
    marginLeft: -40,
    marginRight: 10,
  },
  circleButton: {
    justifyContent: "center",
    alignItems: "center",
    borderRadius: 42,
    backgroundColor: "#134D8B",
  },
  buttonSmall: {
    width: 26,
    height: 26,
    margin: 2,
    alignSelf: "flex-start",
  },
  buttonLarge: {
    width: 30,
    height: 30,
  },
});
