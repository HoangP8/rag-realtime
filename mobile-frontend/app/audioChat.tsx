import React, { useState } from "react";
import { View, Text, TouchableOpacity, StyleSheet } from "react-native";
import { useRouter } from "expo-router";
import Ionicons from "react-native-vector-icons/Ionicons";

export default function AudioChat() {
  const router = useRouter();
  const [isRecording, setIsRecording] = useState(false);

  const startRecording = async () => {
    setIsRecording(true);
  };

  const stopRecording = async () => {
    setIsRecording(false);
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Live Audio Chat</Text>

      <View style={styles.buttonContainer}>
        <TouchableOpacity
          style={[styles.roundButton, isRecording ? styles.recording : null]}
          onPress={isRecording ? stopRecording : startRecording}
        >
          <Ionicons
            name={isRecording ? "stop" : "mic"}
            size={30}
            color="#fff"
          />
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.roundButton, styles.exitButton]}
          onPress={() => router.push("/chat")}
        >
          <Ionicons name="close" size={30} color="#fff" />
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#000",
    alignItems: "center",
    justifyContent: "center",
  },
  title: {
    color: "#fff",
    fontSize: 20,
    marginBottom: 20,
  },
  buttonContainer: {
    position: "absolute",
    bottom: "15%",
    flexDirection: "row",
    justifyContent: "space-between",
    width: "60%",
  },
  roundButton: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: "#1F1F1F",
    alignItems: "center",
    justifyContent: "center",
  },
  recording: {
    backgroundColor: "red",
  },
  exitButton: {
    backgroundColor: "gray",
  },
});
