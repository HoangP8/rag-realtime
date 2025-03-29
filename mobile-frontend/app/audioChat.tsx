import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Animated,
} from "react-native";
import { useRouter } from "expo-router";
import Ionicons from "react-native-vector-icons/Ionicons";
import {
  AudioSession,
  LiveKitRoom,
  registerGlobals,
  useLocalParticipant,
} from "@livekit/react-native";

registerGlobals();
const wsURL = "wss://clinical-chatbot-1dewlazs.livekit.cloud";
const token =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NDMyODAwODgsImlzcyI6IkFQSURlWWRCTGlDZm5WWiIsIm5iZiI6MTc0MzI3Mjg4OCwic3ViIjoicXVpY2tzdGFydCB1c2VyIDNteml4cyIsInZpZGVvIjp7ImNhblB1Ymxpc2giOnRydWUsImNhblB1Ymxpc2hEYXRhIjp0cnVlLCJjYW5TdWJzY3JpYmUiOnRydWUsInJvb20iOiJxdWlja3N0YXJ0IHJvb20iLCJyb29tSm9pbiI6dHJ1ZX19.Xl9qauBcAm4TgSUaXLM551Icmcude_-hG6-RWcDmetQ";

export default function AudioChat() {
  useEffect(() => {
    let start = async () => {
      await AudioSession.startAudioSession();
    };

    start();
    return () => {
      AudioSession.stopAudioSession();
    };
  }, []);
  return (
    <LiveKitRoom
      serverUrl={wsURL}
      token={token}
      connect={true}
      audio={true}
      onConnected={() => console.log("Connected to room")}
      onDisconnected={() => console.log("Disconnected from room")}
    >
      <View style={styles.container}>
        <Text style={styles.title}>Live Audio Chat</Text>

        <ControlButton />
      </View>
    </LiveKitRoom>
  );
}

function ControlButton() {
  const router = useRouter();
  const [isRecording, setIsRecording] = useState(true);
  const { localParticipant } = useLocalParticipant();
  const startRecording = async () => {
    try {
      if (localParticipant) {
        console.log("Attempting to enable microphone");
        await localParticipant.setMicrophoneEnabled(true);
        console.log("Microphone enabled");
      }
      setIsRecording(true);
    } catch (error) {
      console.error("Error enabling microphone:", error);
    }
  };

  const stopRecording = async () => {
    if (localParticipant) {
      await localParticipant.setMicrophoneEnabled(false);
      console.log("Microphone disabled");
    }
    setIsRecording(false);
  };
  return (
    <View style={styles.buttonContainer}>
      <TouchableOpacity
        style={[styles.roundButton, isRecording ? styles.recording : null]}
        onPress={isRecording ? stopRecording : startRecording}
      >
        <Ionicons
          name={isRecording ? "mic" : "mic-off"}
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
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#fff",
    alignItems: "center",
    justifyContent: "center",
  },
  title: {
    color: "#000",
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
    backgroundColor: "#C32229",
    alignItems: "center",
    justifyContent: "center",
  },
  recording: {
    backgroundColor: "#134D8B",
  },
  exitButton: {
    backgroundColor: "#C32229",
  },
});
