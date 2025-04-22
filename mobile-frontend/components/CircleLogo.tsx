import { View, StyleSheet, Image, Text } from "react-native";

type Props = {
  size?: number;
};
export default function CircleLogo({ size = 320 }: Props) {
  return (
    <View style={styles.container}>
      <View style={[styles.logoContainer, { padding: size / 5 }]}>
        <Image
          style={{
            width: size,
            height: size,
            borderRadius: size / 2,
          }}
          source={require("@/assets/images/logo.png")}
          resizeMode="contain"
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: "center",
    justifyContent: "center",
  },
  logoContainer: {
    alignItems: "center",
    justifyContent: "center",
  },
  title: {},
});
